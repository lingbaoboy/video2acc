import subprocess
import json
import os
import re # 用于解析FFmpeg进度信息
import platform # 用于更精确地判断操作系统
import logging

class FFmpegProcessor:
    """
    封装FFmpeg和FFprobe的命令行操作。
    负责探测媒体文件信息、构建FFmpeg命令并执行。
    """
    def __init__(self, log_callback=None):
        """
        初始化FFmpegProcessor。
        Args:
            log_callback (callable, optional): 用于发送日志消息的回调函数。
                                                通常是AppLogger实例的log_gui_message方法。
        """
        self.log_callback = log_callback

        # 获取当前脚本所在目录的绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 构建ffmpeg工具链所在的子目录路径
        ffmpeg_bin_dir = os.path.join(current_dir, "ffmpeg")

        # 根据操作系统设置FFmpeg和FFprobe可执行文件的完整路径
        if platform.system() == 'Windows':
            self.ffprobe_path = os.path.join(ffmpeg_bin_dir, "ffprobe.exe")
            self.ffmpeg_path = os.path.join(ffmpeg_bin_dir, "ffmpeg.exe")
        else: # Linux, macOS, etc.
            self.ffprobe_path = os.path.join(ffmpeg_bin_dir, "ffprobe")
            self.ffmpeg_path = os.path.join(ffmpeg_bin_dir, "ffmpeg")
        
        self._log(f"[INFO] 配置 FFmpeg 路径: {self.ffmpeg_path}")
        self._log(f"[INFO] 配置 FFprobe 路径: {self.ffprobe_path}")

    def _log(self, message, level=logging.INFO):
        """
        内部日志记录方法，通过回调函数将消息发送出去。
        """
        if self.log_callback:
            self.log_callback(message, level=level)
        else:
            print(message) # 如果没有提供回调，则打印到控制台

    def check_ffmpeg_available(self):
        """
        检查指定路径的FFmpeg和FFprobe可执行文件是否存在且可执行。
        """
        if not os.path.exists(self.ffmpeg_path) or not os.path.exists(self.ffprobe_path):
            self._log(f"[ERROR] FFmpeg 或 FFprobe 可执行文件未在预期路径找到。")
            self._log(f"预期 FFmpeg 路径: {self.ffmpeg_path}")
            self._log(f"预期 FFprobe 路径: {self.ffprobe_path}")
            return False
        
        # 尝试运行一下，确保是可执行文件且能正常工作
        try:
            # 短暂运行命令以验证其功能性
            subprocess.run([self.ffmpeg_path, "-version"], check=True, capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0)
            subprocess.run([self.ffprobe_path, "-version"], check=True, capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0)
            self._log("[INFO] FFmpeg 和 FFprobe 已成功验证。")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, PermissionError) as e:
            self._log(f"[ERROR] 验证 FFmpeg/ffprobe 失败: {e}")
            self._log(f"请确保 '{self.ffmpeg_path}' 和 '{self.ffprobe_path}' 是有效的可执行文件，并且具有执行权限。")
            return False
        except Exception as e:
            self._log(f"[ERROR] 验证 FFmpeg/ffprobe 时发生未知错误: {e}")
            return False

    def probe_audio_tracks(self, file_path):
        """
        使用 ffprobe 探测指定文件中的所有音频轨道信息。
        Args:
            file_path (str): 待探测的媒体文件路径。
        Returns:
            list: 一个列表，每个元素是一个字典，包含 'index' (音轨索引), 'codec_name' (编码器名称),
                  'language' (语言标签，如果有的话)。如果失败或无音轨，返回 None 或空列表。
        """
        if not os.path.exists(file_path):
            self._log(f"[ERROR] 文件不存在，无法探测: {file_path}")
            return None

        command = [
            self.ffprobe_path,
            "-v", "error", # 只输出错误信息到stderr
            "-select_streams", "a", # 只选择音频流
            "-show_entries", "stream=index,codec_name,codec_type,tags", # 增加 codec_type 字段
            "-of", "json", # 输出为JSON格式
            file_path
        ]
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError as je:
                self._log(f"[ERROR] ffprobe 输出 JSON 解析失败: {je}")
                self._log(f"ffprobe 原始输出: {result.stdout.strip()}")
                return None

            tracks = []
            if 'streams' in data:
                for stream in data['streams']:
                    tracks.append({
                        'index': stream['index'],
                        'codec_name': stream['codec_name'],
                        'codec_type': stream.get('codec_type', 'audio'),
                        'language': stream.get('tags', {}).get('language', '未知') # 获取语言标签，如果没有则为'未知'
                    })
            return tracks
        except subprocess.CalledProcessError as cpe:
            self._log(f"[ERROR] ffprobe 探测 {file_path} 失败: {cpe.returncode}")
            self._log(f"ffprobe stdout: {cpe.stdout.strip() if cpe.stdout else ''}")
            self._log(f"ffprobe stderr: {cpe.stderr.strip() if cpe.stderr else ''}")
            return None
        except Exception as e:
            self._log(f"[CRITICAL ERROR] ffprobe 探测时发生未知异常: {e}")
            return None

    def _execute_ffmpeg_command(self, cmd_args, input_path, output_path, operation_desc):
        """
        执行 FFmpeg 命令并处理输出。
        Args:
            cmd_args (list): FFmpeg 命令参数列表 (不包含ffmpeg可执行文件本身)。
            input_path (str): 输入文件路径。
            output_path (str): 输出文件路径。
            operation_desc (str): 操作的描述，用于日志记录。
        Returns:
            bool: 命令执行成功返回 True，否则返回 False。
        """
        full_command = [self.ffmpeg_path, '-y'] + cmd_args # 添加 -y 选项以自动覆盖输出文件
        self._log(f"[CMD] {' '.join(full_command)}", level=logging.DEBUG) # 记录完整命令行

        try:
            process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, # FFmpeg的进度和错误信息通常在stderr
                text=True, # 以文本模式处理输出
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )

            # 使用 communicate() 来安全地获取输出，避免死锁
            stdout_output, stderr_output = process.communicate()

            if process.returncode != 0:
                # 如果FFmpeg返回非零码，说明执行失败
                self._log(f"[ERROR] FFmpeg {operation_desc}失败 ({output_path}): 返回码 {process.returncode}")
                self._log(f"FFmpeg stdout:\n{stdout_output.strip()}")
                self._log(f"FFmpeg stderr:\n{stderr_output.strip()}")
                return False
            else:
                self._log(f"[INFO] FFmpeg {operation_desc}成功 ({output_path})")
                self._log(f"FFmpeg stdout:\n{stdout_output.strip()}")
                self._log(f"FFmpeg stderr:\n{stderr_output.strip()}")
                # 检查 stderr 中是否有实际错误，即使返回码为0
                if 'error' in stderr_output.lower() and not 'error reading' in stderr_output.lower(): # 忽略不重要的读取错误
                    self._log(f"[WARNING] FFmpeg 操作成功，但 stderr 中包含潜在错误信息:\n{stderr_output.strip()}")
                return True
        except FileNotFoundError:
            self._log(f"[CRITICAL ERROR] FFmpeg 可执行文件 '{self.ffmpeg_path}' 未找到。请检查路径和权限。")
            return False
        except Exception as e:
            self._log(f"[CRITICAL ERROR] 执行 FFmpeg 命令时发生未知异常 ({operation_desc} {output_path}): {e}")
            return False

    def extract_aac_track(self, input_path, output_path, track_index):
        """
        直接无损提取 AAC 音轨。
        """
        cmd_args = [
            "-i", input_path,
            "-map", f"0:a:{track_index}", # 明确指定音轨索引
            "-c:a", "copy", # 直接复制音频流，不重新编码
            "-movflags", "faststart", # 用于Web播放优化，适用于MP4/M4A
            output_path
        ]
        return self._execute_ffmpeg_command(cmd_args, input_path, output_path, "直接提取 AAC")

    def extract_raw_audio(self, input_path, output_path, track_index, codec_name=None):
        """
        无损提取任意格式的原始音频。
        Args:
            input_path (str): 输入文件路径。
            output_path (str): 输出文件路径。
            track_index (int): 要提取的音轨索引。
            codec_name (str, optional): 原始音频编码名称，用于某些格式的容器推断。
        Returns:
            bool: 操作成功返回 True，否则返回 False。
        """
        cmd_args = [
            "-i", input_path,
            "-map", f"0:a:{track_index}",
            "-c:a", "copy" # 复制原始音频流
        ]
        
        # 针对特定无损格式（如原始PCM）可能需要额外指定输出容器，否则FFmpeg可能无法推断
        if codec_name:
            if codec_name.lower() in ['pcm_s16le', 'pcm_f32le', 'pcm_s24le', 'pcm_s32le']:
                # 对于原始PCM，通常需要指定容器，如wav
                cmd_args.extend(["-f", "wav"])
                self._log(f"[INFO] 检测到PCM原始音频，强制输出容器为 WAV。")
            elif codec_name.lower() == 'truehd': # TrueHD 常用在.mka或.truehd
                cmd_args.extend(["-f", "truehd"])
            # 其他特殊格式可以按需添加

        cmd_args.append(output_path)
        
        return self._execute_ffmpeg_command(cmd_args, input_path, output_path, f"无损提取原始音频 ({codec_name})")

    def recode_audio(self, input_path, output_path, codec, bitrate=None, samplerate=None, channels=None, quality=None, track_index=None):
        """
        将音频重新编码为指定格式。
        Args:
            input_path (str): 输入文件路径。
            output_path (str): 输出文件路径。
            codec (str): 目标音频编码器 (e.g., "aac", "libmp3lame", "libopus", "flac").
                         注意：FFmpeg可能需要对应的库支持 (例如 mp3 需要 libmp3lame)。
            bitrate (str, optional): 音频比特率 (e.g., "192k").
            samplerate (str, optional): 采样率 (e.g., "48000").
            channels (str, optional): 声道数 (e.g., "2").
            quality (str, optional): 质量参数 (具体含义取决于编码器)。
            track_index (int, optional): 如果是从原始媒体文件编码，指定音轨索引。
        Returns:
            bool: 操作成功返回 True，否则返回 False。
        """
        cmd_args = ["-i", input_path]
        if track_index is not None:
            # 如果是从原始媒体文件直接提取并编码，需要指定音轨
            cmd_args.extend(["-map", f"0:a:{track_index}"]) 
            self._log(f"[INFO] 从音轨 {track_index} 提取并编码。")

        # 音频编码器设置
        # 注意：FFmpeg内置的AAC编码器通常是'aac'，但如果编译时支持libfdk_aac，则用'libfdk_aac'
        # MP3编码器通常需要编译时支持libmp3lame，编码器名为'libmp3lame'
        # Opus需要libopus，编码器名为'libopus'
        # FLAC是内置的，编码器名为'flac'
        # AC3是内置的，编码器名为'ac3'
        
        # 默认使用通用名称，如果用户安装的FFmpeg不支持，可能需要更精确的名称
        ffmpeg_codec_name = codec.lower()
        if ffmpeg_codec_name == "mp3":
            ffmpeg_codec_name = "libmp3lame" # 推荐使用libmp3lame获取更好质量
        elif ffmpeg_codec_name == "opus":
            ffmpeg_codec_name = "libopus" # 推荐使用libopus
        
        cmd_args.extend(["-c:a", ffmpeg_codec_name]) 

        # 比特率设置（自动补全单位）
        if bitrate:
            # 某些无损格式如FLAC，比特率通常不直接设置，而是由压缩级别决定
            if ffmpeg_codec_name not in ["flac"]:
                # 自动补全单位（如无k/m结尾则补k）
                br = str(bitrate)
                if br.isdigit():
                    br = br + 'k'
                elif not br.lower().endswith(('k','m')):
                    # 其他情况如128K、128Kbps等，原样传递
                    br = br
                cmd_args.extend(["-b:a", br])
                self._log(f"[INFO] 设置比特率: {br}")
            else:
                self._log(f"[WARNING] 对于 {codec} 编码 (无损)，比特率设置通常被忽略。")

        # 采样率
        if samplerate:
            cmd_args.extend(["-ar", samplerate])
            self._log(f"[INFO] 设置采样率: {samplerate}")
        # 声道数
        if channels:
            cmd_args.extend(["-ac", channels])
            self._log(f"[INFO] 设置声道数: {channels}")
        
        # 质量参数 (CRF/VBR/压缩级别)
        if quality:
            if ffmpeg_codec_name == "aac":
                # 对于FFmpeg内置的AAC编码器，-q:a 是质量参数 (VBR)
                # 范围通常是 0.1-2 (高到低质量)，但有时也用0-100%或CRF风格值，具体取决于FFmpeg版本和编译选项
                # 对于libfdk_aac (如果可用且编译支持)，是 -vbr N，N=1-5
                cmd_args.extend(["-q:a", quality])
                self._log(f"[INFO] {codec} 编码使用质量参数 -q:a {quality}")
            elif ffmpeg_codec_name == "libmp3lame":
                # MP3的VBR质量，-q:a 通常范围 0-9 (0最高质量，9最低)
                cmd_args.extend(["-q:a", quality])
                self._log(f"[INFO] {codec} 编码使用质量参数 -q:a {quality}")
            elif ffmpeg_codec_name == "libopus":
                # Opus 质量通常由比特率控制，但也可以有 -compression_level 或 -vbr_level
                # 简单起见，这里假设用户输入的'quality'可以直接映射到FFmpeg的-vbr N，范围0-10，0最低10最高
                # 或者，更常见的是让它由比特率决定，或使用libopus特有的参数
                # 这里为了演示，我们假设它是一个通用的质量参数
                cmd_args.extend(["-vbr", "on"]) # 确保VBR开启
                cmd_args.extend(["-compression_level", quality]) # 示例：Opus的压缩级别
                self._log(f"[INFO] {codec} 编码使用压缩级别 -compression_level {quality}")
            elif ffmpeg_codec_name == "flac":
                # FLAC的压缩级别，范围0-8 (8是最高压缩)
                cmd_args.extend(["-compression_level", quality])
                self._log(f"[INFO] {codec} 编码使用压缩级别 -compression_level {quality}")
            elif ffmpeg_codec_name == "ac3":
                # AC3 通常用比特率控制质量，很少用独立质量参数
                self._log(f"[WARNING] {codec} 编码不常用独立 '质量' 参数。")
            else:
                self._log(f"[WARNING] 编码器 {codec} 不支持或不需要 '质量' 参数。")
        
        # 最终输出文件
        cmd_args.append(output_path)
        
        return self._execute_ffmpeg_command(cmd_args, input_path, output_path, f"重新编码为 {codec}")

    def get_common_audio_extension(self, codec_name):
        """
        根据 FFmpeg codec_name 返回常见的音频文件扩展名。
        Args:
            codec_name (str): FFmpeg 探测到的编码器名称。
        Returns:
            str: 常见的音频文件扩展名，默认为 "bin"。
        """
        codec_map = {
            "mp3": "mp3",
            "aac": "aac", # 裸AAC流
            "ac3": "ac3",
            "eac3": "eac3",
            "dts": "dts",
            "dtshd": "dts",
            "flac": "flac",
            "alac": "m4a", # ALAC也常在m4a中
            "pcm_s16le": "wav", # PCM通常在WAV中
            "pcm_f32le": "wav",
            "pcm_s24le": "wav",
            "pcm_s32le": "wav",
            "opus": "opus",
            "vorbis": "ogg",
            "wma": "wma", # Windows Media Audio
            "truehd": "truehd", # TrueHD
            "mlp": "mlp", # Meridian Lossless Packing (常用于Dolby TrueHD)
            # 根据需要添加更多映射
        }
        return codec_map.get(codec_name.lower(), "bin") # 默认为bin，表示未知二进制流