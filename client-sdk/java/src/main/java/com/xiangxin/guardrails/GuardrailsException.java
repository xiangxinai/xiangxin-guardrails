package com.xiangxin.guardrails;

/**
 * 护栏系统基础异常类
 */
public class GuardrailsException extends Exception {
    private final String code;

    public GuardrailsException(String message) {
        super(message);
        this.code = null;
    }

    public GuardrailsException(String message, Throwable cause) {
        super(message, cause);
        this.code = null;
    }

    public GuardrailsException(String message, String code) {
        super(message);
        this.code = code;
    }

    public GuardrailsException(String message, String code, Throwable cause) {
        super(message, cause);
        this.code = code;
    }

    public String getCode() {
        return code;
    }
}

/**
 * 认证异常
 */
class AuthenticationException extends GuardrailsException {
    public AuthenticationException(String message) {
        super(message);
    }

    public AuthenticationException(String message, Throwable cause) {
        super(message, cause);
    }
}

/**
 * 数据验证异常
 */
class ValidationException extends GuardrailsException {
    public ValidationException(String message) {
        super(message);
    }

    public ValidationException(String message, Throwable cause) {
        super(message, cause);
    }
}

/**
 * 资源不存在异常
 */
class NotFoundException extends GuardrailsException {
    public NotFoundException(String message) {
        super(message);
    }

    public NotFoundException(String message, Throwable cause) {
        super(message, cause);
    }
}

/**
 * 请求频率限制异常
 */
class RateLimitException extends GuardrailsException {
    public RateLimitException(String message) {
        super(message);
    }

    public RateLimitException(String message, Throwable cause) {
        super(message, cause);
    }
}
