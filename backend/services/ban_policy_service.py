"""
封禁策略服务模块
负责封禁策略的管理、用户封禁检查和记录
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from database.connection import get_admin_db_session
import logging
import uuid

logger = logging.getLogger(__name__)

def utcnow():
    """获取当前UTC时间（timezone-aware）"""
    return datetime.now(timezone.utc)


class BanPolicyService:
    """封禁策略服务类"""

    @staticmethod
    async def get_ban_policy(tenant_id: str) -> Optional[Dict[str, Any]]:
        """获取租户的封禁策略配置"""
        db = get_admin_db_session()
        try:
            result = db.execute(
                text("""
                SELECT id, tenant_id, enabled, risk_level, trigger_count,
                       time_window_minutes, ban_duration_minutes,
                       created_at, updated_at
                FROM ban_policies
                WHERE tenant_id = :tenant_id
                """),
                {"tenant_id": tenant_id}
            )
            row = result.fetchone()
            if row:
                return {
                    'id': str(row[0]),
                    'tenant_id': str(row[1]),
                    'enabled': row[2],
                    'risk_level': row[3],
                    'trigger_count': row[4],
                    'time_window_minutes': row[5],
                    'ban_duration_minutes': row[6],
                    'created_at': row[7],
                    'updated_at': row[8]
                }
            return None
        finally:
            db.close()

    @staticmethod
    async def update_ban_policy(tenant_id: str, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新封禁策略配置"""
        db = get_admin_db_session()
        try:
            # 检查策略是否存在
            result = db.execute(
                text("SELECT id FROM ban_policies WHERE tenant_id = :tenant_id"),
                {"tenant_id": tenant_id}
            )
            existing = result.fetchone()

            if existing:
                # 更新现有策略
                result = db.execute(
                    text("""
                    UPDATE ban_policies
                    SET enabled = :enabled,
                        risk_level = :risk_level,
                        trigger_count = :trigger_count,
                        time_window_minutes = :time_window_minutes,
                        ban_duration_minutes = :ban_duration_minutes,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE tenant_id = :tenant_id
                    RETURNING id, tenant_id, enabled, risk_level, trigger_count,
                              time_window_minutes, ban_duration_minutes,
                              created_at, updated_at
                    """),
                    {
                        "tenant_id": tenant_id,
                        "enabled": policy_data.get('enabled', False),
                        "risk_level": policy_data.get('risk_level', '高风险'),
                        "trigger_count": policy_data.get('trigger_count', 3),
                        "time_window_minutes": policy_data.get('time_window_minutes', 10),
                        "ban_duration_minutes": policy_data.get('ban_duration_minutes', 60)
                    }
                )
                db.commit()
            else:
                # 创建新策略
                result = db.execute(
                    text("""
                    INSERT INTO ban_policies (tenant_id, enabled, risk_level, trigger_count,
                                             time_window_minutes, ban_duration_minutes)
                    VALUES (:tenant_id, :enabled, :risk_level, :trigger_count,
                            :time_window_minutes, :ban_duration_minutes)
                    RETURNING id, tenant_id, enabled, risk_level, trigger_count,
                              time_window_minutes, ban_duration_minutes,
                              created_at, updated_at
                    """),
                    {
                        "tenant_id": tenant_id,
                        "enabled": policy_data.get('enabled', False),
                        "risk_level": policy_data.get('risk_level', '高风险'),
                        "trigger_count": policy_data.get('trigger_count', 3),
                        "time_window_minutes": policy_data.get('time_window_minutes', 10),
                        "ban_duration_minutes": policy_data.get('ban_duration_minutes', 60)
                    }
                )
                db.commit()

            row = result.fetchone()
            return {
                'id': str(row[0]),
                'tenant_id': str(row[1]),
                'enabled': row[2],
                'risk_level': row[3],
                'trigger_count': row[4],
                'time_window_minutes': row[5],
                'ban_duration_minutes': row[6],
                'created_at': row[7],
                'updated_at': row[8]
            }
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    @staticmethod
    async def check_user_banned(tenant_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """检查用户是否被封禁"""
        db = get_admin_db_session()
        try:
            result = db.execute(
                text("""
                SELECT id, user_id, banned_at, ban_until, trigger_count,
                       risk_level, reason
                FROM user_ban_records
                WHERE tenant_id = :tenant_id
                  AND user_id = :user_id
                  AND is_active = true
                  AND ban_until > CURRENT_TIMESTAMP
                ORDER BY banned_at DESC
                LIMIT 1
                """),
                {"tenant_id": tenant_id, "user_id": user_id}
            )
            row = result.fetchone()
            if row:
                return {
                    'id': str(row[0]),
                    'user_id': row[1],
                    'banned_at': row[2],
                    'ban_until': row[3],
                    'trigger_count': row[4],
                    'risk_level': row[5],
                    'reason': row[6]
                }
            return None
        finally:
            db.close()

    @staticmethod
    async def check_and_apply_ban_policy(
        tenant_id: str,
        user_id: str,
        risk_level: str,
        detection_result_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """检查并应用封禁策略"""
        logger.info(f"check_and_apply_ban_policy called: tenant_id={tenant_id}, user_id={user_id}, risk_level={risk_level}")
        db = get_admin_db_session()
        try:
            # 获取封禁策略
            logger.info(f"Fetching ban policy for tenant_id={tenant_id}")
            policy_result = db.execute(
                text("""
                SELECT enabled, risk_level, trigger_count, time_window_minutes, ban_duration_minutes
                FROM ban_policies
                WHERE tenant_id = :tenant_id
                """),
                {"tenant_id": tenant_id}
            )
            policy = policy_result.fetchone()
            logger.info(f"Ban policy fetched: {policy}")

            # 如果策略不存在或未启用，直接返回
            if not policy or not policy[0]:  # enabled
                logger.info(f"Ban policy not found or disabled for tenant_id={tenant_id}")
                return None

            policy_risk_level = policy[1]
            trigger_count = policy[2]
            time_window_minutes = policy[3]
            ban_duration_minutes = policy[4]
            logger.info(f"Policy config: risk_level={policy_risk_level}, trigger_count={trigger_count}, window={time_window_minutes}min, duration={ban_duration_minutes}min")

            # 风险等级映射
            risk_level_map = {'低风险': 1, '中风险': 2, '高风险': 3}
            current_risk_value = risk_level_map.get(risk_level, 0)
            policy_risk_value = risk_level_map.get(policy_risk_level, 3)
            logger.info(f"Risk level check: current={risk_level}({current_risk_value}), policy={policy_risk_level}({policy_risk_value})")

            # 如果当前风险等级低于策略要求的等级，不记录
            if current_risk_value < policy_risk_value:
                logger.info(f"Risk level below policy threshold, skipping")
                return None

            # 记录风险触发
            logger.info(f"Recording risk trigger for user_id={user_id}")
            db.execute(
                text("""
                INSERT INTO user_risk_triggers (tenant_id, user_id, detection_result_id, risk_level, triggered_at)
                VALUES (:tenant_id, :user_id, :detection_result_id, :risk_level, CURRENT_TIMESTAMP)
                """),
                {
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "detection_result_id": detection_result_id,
                    "risk_level": risk_level
                }
            )
            db.commit()
            logger.info(f"Risk trigger recorded successfully")

            # 计算时间窗口起点
            window_start = utcnow() - timedelta(minutes=time_window_minutes)
            logger.info(f"Checking triggers since {window_start}")

            # 统计时间窗口内的触发次数
            count_result = db.execute(
                text("""
                SELECT COUNT(*) FROM user_risk_triggers
                WHERE tenant_id = :tenant_id
                  AND user_id = :user_id
                  AND risk_level = :risk_level
                  AND triggered_at > :window_start
                """),
                {
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "risk_level": policy_risk_level,
                    "window_start": window_start
                }
            )
            trigger_count_actual = count_result.scalar()
            logger.info(f"Trigger count in window: {trigger_count_actual}/{trigger_count}")

            # 如果达到阈值，创建封禁记录
            if trigger_count_actual >= trigger_count:
                logger.info(f"Trigger count threshold reached, creating ban record")
                # 检查是否已有活跃的封禁记录
                existing_result = db.execute(
                    text("""
                    SELECT id FROM user_ban_records
                    WHERE tenant_id = :tenant_id
                      AND user_id = :user_id
                      AND is_active = true
                      AND ban_until > CURRENT_TIMESTAMP
                    """),
                    {"tenant_id": tenant_id, "user_id": user_id}
                )
                existing_ban = existing_result.fetchone()

                if not existing_ban:
                    logger.info(f"No existing ban found, creating new ban record")
                    # 创建新的封禁记录
                    ban_until = utcnow() + timedelta(minutes=ban_duration_minutes)
                    reason = f"在 {time_window_minutes} 分钟内触发 {trigger_count_actual} 次{policy_risk_level}风险"

                    result = db.execute(
                        text("""
                        INSERT INTO user_ban_records (
                            tenant_id, user_id, banned_at, ban_until,
                            trigger_count, risk_level, reason, is_active
                        )
                        VALUES (
                            :tenant_id, :user_id, CURRENT_TIMESTAMP, :ban_until,
                            :trigger_count, :risk_level, :reason, true
                        )
                        RETURNING id, user_id, banned_at, ban_until, trigger_count, risk_level, reason
                        """),
                        {
                            "tenant_id": tenant_id,
                            "user_id": user_id,
                            "ban_until": ban_until,
                            "trigger_count": trigger_count_actual,
                            "risk_level": policy_risk_level,
                            "reason": reason
                        }
                    )
                    db.commit()

                    row = result.fetchone()
                    logger.warning(f"用户 {user_id} 已被封禁至 {ban_until}，原因：{reason}")

                    return {
                        'id': str(row[0]),
                        'user_id': row[1],
                        'banned_at': row[2],
                        'ban_until': row[3],
                        'trigger_count': row[4],
                        'risk_level': row[5],
                        'reason': row[6]
                    }
                else:
                    logger.info(f"User already has active ban, skipping")
            else:
                logger.info(f"Trigger count below threshold, not banning")

            return None

        except Exception as e:
            logger.error(f"Error in check_and_apply_ban_policy: {e}", exc_info=True)
            db.rollback()
            logger.error(f"应用封禁策略失败: {e}")
            raise e
        finally:
            db.close()

    @staticmethod
    async def get_banned_users(tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取被封禁用户列表"""
        db = get_admin_db_session()
        try:
            result = db.execute(
                text("""
                SELECT id, user_id, banned_at, ban_until, trigger_count,
                       risk_level, reason, is_active,
                       CASE
                           WHEN ban_until > CURRENT_TIMESTAMP THEN '封禁中'
                           ELSE '已解封'
                       END as status
                FROM user_ban_records
                WHERE tenant_id = :tenant_id
                ORDER BY banned_at DESC
                LIMIT :limit OFFSET :skip
                """),
                {"tenant_id": tenant_id, "skip": skip, "limit": limit}
            )

            users = []
            for row in result.fetchall():
                users.append({
                    'id': str(row[0]),
                    'user_id': row[1],
                    'banned_at': row[2],
                    'ban_until': row[3],
                    'trigger_count': row[4],
                    'risk_level': row[5],
                    'reason': row[6],
                    'is_active': row[7],
                    'status': row[8]
                })

            return users
        finally:
            db.close()

    @staticmethod
    async def unban_user(tenant_id: str, user_id: str) -> bool:
        """手动解封用户"""
        db = get_admin_db_session()
        try:
            result = db.execute(
                text("""
                UPDATE user_ban_records
                SET is_active = false, ban_until = CURRENT_TIMESTAMP
                WHERE tenant_id = :tenant_id
                  AND user_id = :user_id
                  AND is_active = true
                """),
                {"tenant_id": tenant_id, "user_id": user_id}
            )
            db.commit()

            affected_rows = result.rowcount
            if affected_rows > 0:
                logger.info(f"用户 {user_id} 已被手动解封")
                return True
            return False

        except Exception as e:
            db.rollback()
            logger.error(f"解封用户失败: {e}")
            raise e
        finally:
            db.close()

    @staticmethod
    async def get_user_risk_history(
        tenant_id: str,
        user_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """获取用户风险触发历史"""
        db = get_admin_db_session()
        try:
            since = utcnow() - timedelta(days=days)

            result = db.execute(
                text("""
                SELECT id, detection_result_id, risk_level, triggered_at
                FROM user_risk_triggers
                WHERE tenant_id = :tenant_id
                  AND user_id = :user_id
                  AND triggered_at > :since
                ORDER BY triggered_at DESC
                """),
                {"tenant_id": tenant_id, "user_id": user_id, "since": since}
            )

            history = []
            for row in result.fetchall():
                history.append({
                    'id': str(row[0]),
                    'detection_result_id': str(row[1]) if row[1] else None,
                    'risk_level': row[2],
                    'triggered_at': row[3]
                })

            return history
        finally:
            db.close()
