import React, { useState } from 'react';
import { Upload, Button, Image, Space, message, Card } from 'antd';
import { PlusOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';

interface ImageUploadProps {
  onChange?: (base64Images: string[]) => void;
  maxCount?: number;
  maxSize?: number; // MB
}

const ImageUpload: React.FC<ImageUploadProps> = ({
  onChange,
  maxCount = 5,
  maxSize = 10
}) => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [previewImage, setPreviewImage] = useState('');
  const [previewOpen, setPreviewOpen] = useState(false);

  // 将文件转换为base64
  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          resolve(reader.result);
        } else {
          reject(new Error('Failed to read file'));
        }
      };
      reader.onerror = (error) => reject(error);
    });
  };

  // 获取图片格式
  const getImageFormat = (mimeType: string): string => {
    const formats: Record<string, string> = {
      'image/jpeg': 'jpeg',
      'image/jpg': 'jpeg',
      'image/png': 'png',
      'image/gif': 'gif',
      'image/bmp': 'bmp',
      'image/webp': 'webp',
      'image/tiff': 'tiff'
    };
    return formats[mimeType] || 'jpeg';
  };

  // 处理文件选择
  const handleChange = async (info: any) => {
    let newFileList = [...info.fileList];

    // 限制数量
    if (newFileList.length > maxCount) {
      message.warning(`最多只能上传${maxCount}张图片`);
      newFileList = newFileList.slice(0, maxCount);
    }

    setFileList(newFileList);

    // 转换所有文件为base64
    try {
      const base64List: string[] = [];
      for (const file of newFileList) {
        if (file.originFileObj) {
          const base64 = await fileToBase64(file.originFileObj as File);
          base64List.push(base64);
        }
      }
      onChange?.(base64List);
    } catch (error) {
      console.error('Failed to convert images to base64:', error);
      message.error('图片处理失败');
    }
  };

  // 上传前的验证
  const beforeUpload = (file: File) => {
    // 验证文件类型
    const isImage = file.type.startsWith('image/');
    if (!isImage) {
      message.error('只能上传图片文件！');
      return Upload.LIST_IGNORE;
    }

    // 验证文件大小
    const isLtMaxSize = file.size / 1024 / 1024 < maxSize;
    if (!isLtMaxSize) {
      message.error(`图片大小不能超过${maxSize}MB！`);
      return Upload.LIST_IGNORE;
    }

    return false; // 阻止自动上传
  };

  // 预览图片
  const handlePreview = async (file: UploadFile) => {
    if (!file.url && !file.preview && file.originFileObj) {
      file.preview = await fileToBase64(file.originFileObj as File);
    }
    setPreviewImage(file.url || file.preview || '');
    setPreviewOpen(true);
  };

  // 移除图片
  const handleRemove = (file: UploadFile) => {
    const newFileList = fileList.filter(item => item.uid !== file.uid);
    setFileList(newFileList);

    // 更新base64列表
    const updateBase64List = async () => {
      const base64List: string[] = [];
      for (const f of newFileList) {
        if (f.originFileObj) {
          const base64 = await fileToBase64(f.originFileObj as File);
          base64List.push(base64);
        }
      }
      onChange?.(base64List);
    };
    updateBase64List();
  };

  const uploadButton = (
    <div>
      <PlusOutlined />
      <div style={{ marginTop: 8 }}>上传图片</div>
    </div>
  );

  return (
    <>
      <Upload
        listType="picture-card"
        fileList={fileList}
        beforeUpload={beforeUpload}
        onChange={handleChange}
        onPreview={handlePreview}
        onRemove={handleRemove}
        multiple
        accept="image/*"
      >
        {fileList.length >= maxCount ? null : uploadButton}
      </Upload>
      {previewImage && (
        <Image
          wrapperStyle={{ display: 'none' }}
          preview={{
            visible: previewOpen,
            onVisibleChange: (visible) => setPreviewOpen(visible),
          }}
          src={previewImage}
        />
      )}
      <div style={{ marginTop: 8, color: '#666', fontSize: 12 }}>
        支持格式：JPEG, PNG, GIF, BMP, WEBP, TIFF | 单张最大{maxSize}MB | 最多{maxCount}张
      </div>
    </>
  );
};

export default ImageUpload;