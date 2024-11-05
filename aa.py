import asyncio
import websockets
import json
import pyaudio
import wave

class VoskStreamingClient:
    def __init__(self, server_url='ws://84.247.183.48:2700'):
        self.server_url = server_url
        
        # 音频参数配置
        self.CHUNK = 8000  # Vosk推荐的块大小
        self.FORMAT = pyaudio.paInt16  # 16位深度
        self.CHANNELS = 1   # 单声道
        self.RATE = 16000  # 采样率16k
        
        # 初始化PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
    async def connect_websocket(self):
        """建立WebSocket连接"""
        async with websockets.connect(self.server_url) as websocket:
            # 发送配置信息 - 这里指定中文模型和采样率
            config = {
                "config": {
                    "sample_rate": 16000,
                    "model": "vosk-model-cn-0.22",  # 指定中文模型
                    "language": "zh"  # 设置语言为中文
                }
            }
            await websocket.send(json.dumps(config))
            
            # 开启音频流
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            print("开始录音...")
            
            try:
                while True:
                    # 读取音频数据
                    data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                    
                    # 发送音频数据
                    await websocket.send(data)
                    
                    # 接收识别结果
                    result = await websocket.recv()
                    result = json.loads(result)
                    
                    # 处理识别结果
                    if 'partial' in result:
                        print(f"部分识别结果: {result['partial']}")
                    if 'result' in result:
                        print(f"完整识别结果: {result['text']}")
                        
                        # 检查是否包含唤醒词
                        if '小爱同学' in result['text'].replace(' ', ''):
                            print("检测到唤醒词!")
                        
            except websockets.exceptions.ConnectionClosedError:
                print("WebSocket连接关闭")
            except KeyboardInterrupt:
                print("停止录音...")
            finally:
                # 清理资源
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()
                self.audio.terminate()

    def start(self):
        """启动客户端"""
        asyncio.get_event_loop().run_until_complete(self.connect_websocket())

# 使用示例
if __name__ == "__main__":
    client = VoskStreamingClient()
    client.start()
