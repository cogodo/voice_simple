import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:socket_io_client/socket_io_client.dart' as io;
import 'lib/services/streaming_audio_service.dart';

/// Comprehensive audio streaming test with detailed timing analysis and live audio playback
class AudioStreamingTest {
  // Test configuration
  static const String WEBSOCKET_URL = 'http://localhost:8000';
  static const String TEST_TEXT =
      'Hello! This is a comprehensive test of the Cartesia audio streaming system. We are testing packet timing, delivery rates, and overall performance metrics. The audio should be playing live during this test.';
  static const String OUTPUT_FILE = 'audio_streaming_test_results.json';

  // Timing tracking
  late DateTime _testStartTime;
  DateTime? _firstFrameTime;
  DateTime? _lastFrameTime;
  final List<Map<String, dynamic>> _frameLog = [];
  final List<Map<String, dynamic>> _eventLog = [];
  final List<Map<String, dynamic>> _consoleLog =
      []; // Capture all console output

  // Performance metrics
  int _framesReceived = 0;
  int _totalBytes = 0;
  double? _previousFrameTime;
  final List<double> _frameIntervals = [];

  // WebSocket connection
  io.Socket? _socket;
  bool _isConnected = false;
  bool _isStreaming = false;

  // Audio playback integration
  StreamingAudioService? _audioService;
  bool _audioInitialized = false;
  Map<String, dynamic> _audioMetrics = {};

  /// Enhanced print function that logs to both console and file
  void _logPrint(String message, {String level = 'INFO'}) {
    print(message); // Still print to console

    // Also log to our comprehensive log
    _consoleLog.add({
      'timestamp': DateTime.now().toIso8601String(),
      'relative_time_ms':
          DateTime.now().difference(_testStartTime).inMilliseconds,
      'level': level,
      'message': message,
    });
  }

  /// Run the complete test with live audio playback
  Future<void> runTest() async {
    _testStartTime = DateTime.now();

    _logPrint(
        '🧪 Starting Cartesia Audio Streaming Test with Live Audio Playback');
    _logPrint(
        '📝 Test will log all packet times and write results to: $OUTPUT_FILE');
    _logPrint('🎵 Audio will stream live during testing for complete analysis');

    _logEvent('test_started', {'start_time': _testStartTime.toIso8601String()});

    try {
      // Phase 1: Initialize audio system
      await _initializeAudioSystem();

      // Phase 2: Connect to WebSocket
      await _connectWebSocket();

      // Phase 3: Start audio streaming
      await _startAudioStreaming();

      // Phase 4: Wait for completion
      await _waitForCompletion();

      // Phase 5: Generate and save report
      await _generateReport();
    } catch (e, stackTrace) {
      _logPrint('❌ Test failed: $e', level: 'ERROR');
      _logEvent('test_error',
          {'error': e.toString(), 'stack_trace': stackTrace.toString()});
    } finally {
      await _cleanup();
    }
  }

  /// Initialize the streaming audio system
  Future<void> _initializeAudioSystem() async {
    _logPrint('🔧 Initializing StreamingAudioService for live playback...');

    try {
      _audioService = StreamingAudioService();
      _audioInitialized = await _audioService!.initialize();

      if (_audioInitialized) {
        _logPrint('✅ Audio system initialized successfully');
        _logEvent('audio_system_initialized', {
          'strategy': _audioService!.getBufferStatus()['strategy'],
          'initialization_time': DateTime.now().toIso8601String()
        });

        // Start monitoring audio service status
        _audioService!.statusStream?.listen((status) {
          _logPrint('🎵 Audio Status: $status', level: 'AUDIO');
          _logEvent('audio_status_update', {'status': status});
        });
      } else {
        _logPrint('❌ Failed to initialize audio system', level: 'ERROR');
        _logEvent('audio_system_failed', {'error': 'Initialization failed'});
      }
    } catch (e) {
      _logPrint('❌ Audio system initialization error: $e', level: 'ERROR');
      _logEvent('audio_system_error', {'error': e.toString()});
    }
  }

  /// Connect to WebSocket server
  Future<void> _connectWebSocket() async {
    _logPrint('🔗 Connecting to WebSocket at $WEBSOCKET_URL...');

    final connectStartTime = DateTime.now();
    _logEvent('websocket_connect_start', {'url': WEBSOCKET_URL});

    _socket = io.io(
        WEBSOCKET_URL,
        io.OptionBuilder()
            .setTransports(['websocket'])
            .disableAutoConnect()
            .build());

    // Connection event handlers
    _socket!.onConnect((_) {
      final connectTime = DateTime.now();
      final duration = connectTime.difference(connectStartTime);
      _isConnected = true;
      _logPrint('✅ Connected to WebSocket (${duration.inMilliseconds}ms)');
      _logEvent('websocket_connected', {
        'duration_ms': duration.inMilliseconds,
        'connect_time': connectTime.toIso8601String()
      });
    });

    _socket!.onDisconnect((_) {
      _isConnected = false;
      _logPrint('🔌 Disconnected from WebSocket');
      _logEvent('websocket_disconnected',
          {'disconnect_time': DateTime.now().toIso8601String()});
    });

    _socket!.onError((error) {
      _logPrint('❌ WebSocket error: $error', level: 'ERROR');
      _logEvent('websocket_error', {'error': error.toString()});
    });

    // PCM frame handler - the main data we're testing
    _socket!.on('pcm_frame', (data) {
      _handlePcmFrame(data);
    });

    // TTS event handlers
    _socket!.on('tts_started', (data) {
      final startTime = DateTime.now();
      _isStreaming = true;
      _logPrint('🎤 TTS streaming started');
      _logEvent('tts_started',
          {'start_time': startTime.toIso8601String(), 'data': data});

      // Start audio streaming if initialized
      if (_audioInitialized) {
        _audioService!.startStreaming();
        _logPrint('🎵 Audio playback started');
        _logEvent('audio_playback_started',
            {'start_time': startTime.toIso8601String()});
      }
    });

    _socket!.on('tts_completed', (data) {
      final endTime = DateTime.now();
      _isStreaming = false;
      _lastFrameTime = endTime;
      _logPrint('🏁 TTS streaming completed');
      _logEvent('tts_completed',
          {'end_time': endTime.toIso8601String(), 'data': data});
    });

    _socket!.on('tts_error', (data) {
      _logPrint('❌ TTS error: $data', level: 'ERROR');
      _logEvent('tts_error', {'error': data});
    });

    // Connect with timeout
    _socket!.connect();

    // Wait for connection with timeout
    const maxWaitTime = Duration(seconds: 10);
    final startWait = DateTime.now();

    while (
        !_isConnected && DateTime.now().difference(startWait) < maxWaitTime) {
      await Future.delayed(Duration(milliseconds: 100));
    }

    if (!_isConnected) {
      throw Exception(
          'Failed to connect to WebSocket within ${maxWaitTime.inSeconds}s');
    }
  }

  /// Start audio streaming from Cartesia
  Future<void> _startAudioStreaming() async {
    if (!_isConnected) {
      throw Exception('Cannot start streaming - WebSocket not connected');
    }

    _logPrint(
        '🎵 Starting audio streaming for text: "${TEST_TEXT.substring(0, 50)}..."');

    final requestTime = DateTime.now();
    _logEvent('tts_request_sent', {
      'request_time': requestTime.toIso8601String(),
      'text': TEST_TEXT,
      'text_length': TEST_TEXT.length
    });

    // Send TTS request
    _socket!.emit('start_tts', {
      'text': TEST_TEXT,
      'voice_id': 'default',
      'request_id': 'test_${requestTime.millisecondsSinceEpoch}'
    });

    _logPrint('📡 TTS request sent');
  }

  /// Handle incoming PCM frame data with live audio playback
  void _handlePcmFrame(dynamic data) {
    final frameTime = DateTime.now();
    _framesReceived++;

    // First frame special handling
    if (_firstFrameTime == null) {
      _firstFrameTime = frameTime;
      final timeToFirstFrame = frameTime.difference(_testStartTime);
      _logPrint(
          '🎯 First frame received after ${timeToFirstFrame.inMilliseconds}ms');
      _logEvent('first_frame_received', {
        'time_to_first_frame_ms': timeToFirstFrame.inMilliseconds,
        'first_frame_time': frameTime.toIso8601String()
      });
    }

    // Convert data and calculate metrics
    final frameData = (data as List).cast<int>();
    final frameBytes = frameData.length;
    _totalBytes += frameBytes;

    // Calculate frame interval
    final currentFrameTimeMs = frameTime.millisecondsSinceEpoch / 1000.0;
    double? intervalMs;

    if (_previousFrameTime != null) {
      intervalMs = (currentFrameTimeMs - _previousFrameTime!) * 1000;
      _frameIntervals.add(intervalMs);
    }

    _previousFrameTime = currentFrameTimeMs;

    // FEED AUDIO TO STREAMING SERVICE for live playback
    if (_audioInitialized && _audioService != null) {
      try {
        _audioService!.addAudioChunk(frameData);

        // Capture audio buffer status every 10 frames
        if (_framesReceived % 10 == 0) {
          final bufferStatus = _audioService!.getBufferStatus();
          _audioMetrics = bufferStatus;

          if (_framesReceived % 50 == 0) {
            _logPrint(
                '🎵 Audio Buffer: ${bufferStatus['buffer_frames']}f (${bufferStatus['buffer_size_ms']}ms), '
                'Underruns: ${bufferStatus['underrun_count']}',
                level: 'AUDIO');
          }
        }
      } catch (e) {
        _logPrint('❌ Error feeding audio: $e', level: 'ERROR');
      }
    }

    // Log frame details
    final frameLog = {
      'frame_number': _framesReceived,
      'timestamp': frameTime.toIso8601String(),
      'timestamp_ms': frameTime.millisecondsSinceEpoch,
      'relative_time_ms': frameTime.difference(_testStartTime).inMilliseconds,
      'frame_bytes': frameBytes,
      'total_bytes_received': _totalBytes,
      'interval_from_previous_ms': intervalMs,
      'audio_time_seconds': _framesReceived * 0.02, // 20ms frames
      'audio_buffer_status':
          _audioMetrics.isNotEmpty ? Map.from(_audioMetrics) : null,
    };

    _frameLog.add(frameLog);

    // Progress logging
    if (_framesReceived % 25 == 0) {
      final avgInterval = _frameIntervals.isNotEmpty
          ? _frameIntervals.reduce((a, b) => a + b) / _frameIntervals.length
          : 0.0;
      final fps = _frameIntervals.isNotEmpty ? 1000.0 / avgInterval : 0.0;

      final audioInfo = _audioMetrics.isNotEmpty
          ? 'Audio: ${_audioMetrics['buffer_frames']}f/${_audioMetrics['buffer_size_ms']}ms, Underruns: ${_audioMetrics['underrun_count']}'
          : 'Audio: N/A';

      _logPrint(
          '📦 Frame $_framesReceived: ${frameBytes}B, interval: ${intervalMs?.toStringAsFixed(1)}ms, '
          'avg: ${avgInterval.toStringAsFixed(1)}ms (${fps.toStringAsFixed(1)} fps), $audioInfo');
    }
  }

  /// Wait for streaming to complete
  Future<void> _waitForCompletion() async {
    _logPrint('⏳ Waiting for streaming to complete...');

    const maxWaitTime = Duration(minutes: 2);
    final startWait = DateTime.now();

    // Wait for streaming to start
    while (
        !_isStreaming && DateTime.now().difference(startWait) < maxWaitTime) {
      await Future.delayed(Duration(milliseconds: 100));
    }

    if (!_isStreaming) {
      throw Exception('Streaming did not start within timeout');
    }

    // Wait for streaming to complete
    while (_isStreaming && DateTime.now().difference(startWait) < maxWaitTime) {
      await Future.delayed(Duration(milliseconds: 100));
    }

    // Give more time for audio to finish playing
    _logPrint('⏳ Waiting additional time for audio playback to complete...');
    await Future.delayed(Duration(milliseconds: 2000));

    final totalDuration = DateTime.now().difference(_testStartTime);
    _logPrint('✅ Streaming completed in ${totalDuration.inMilliseconds}ms');

    // Capture final audio metrics
    if (_audioService != null) {
      final finalAudioStatus = _audioService!.getBufferStatus();
      _logPrint(
          '🎵 Final Audio Status: ${finalAudioStatus['frames_received']} received, '
          '${finalAudioStatus['frames_played']} played, '
          '${finalAudioStatus['underrun_count']} underruns',
          level: 'AUDIO');

      _logEvent('final_audio_metrics', finalAudioStatus);
    }

    _logEvent('streaming_completed', {
      'total_duration_ms': totalDuration.inMilliseconds,
      'frames_received': _framesReceived,
      'total_bytes': _totalBytes,
      'final_audio_metrics': _audioService?.getBufferStatus()
    });
  }

  /// Generate comprehensive test report
  Future<void> _generateReport() async {
    _logPrint('📊 Generating comprehensive test report...');

    final testEndTime = DateTime.now();
    final totalTestDuration = testEndTime.difference(_testStartTime);
    final streamingDuration = _lastFrameTime != null && _firstFrameTime != null
        ? _lastFrameTime!.difference(_firstFrameTime!)
        : Duration.zero;

    // Calculate statistics
    final avgInterval = _frameIntervals.isNotEmpty
        ? _frameIntervals.reduce((a, b) => a + b) / _frameIntervals.length
        : 0.0;

    final minInterval = _frameIntervals.isNotEmpty
        ? _frameIntervals.reduce((a, b) => a < b ? a : b)
        : 0.0;
    final maxInterval = _frameIntervals.isNotEmpty
        ? _frameIntervals.reduce((a, b) => a > b ? a : b)
        : 0.0;

    // Calculate frame rate statistics
    final avgFps = avgInterval > 0 ? 1000.0 / avgInterval : 0.0;
    final expectedFrames =
        (streamingDuration.inMilliseconds / 20).round(); // 20ms frames
    final frameDeliveryRate =
        expectedFrames > 0 ? (_framesReceived / expectedFrames) * 100 : 0.0;

    // Frame timing analysis
    int fastFrames = 0;
    int slowFrames = 0;
    int normalFrames = 0;

    for (final interval in _frameIntervals) {
      if (interval < 15)
        fastFrames++;
      else if (interval > 25)
        slowFrames++;
      else
        normalFrames++;
    }

    // Get final audio metrics
    final finalAudioMetrics = _audioService?.getBufferStatus() ?? {};

    // Build comprehensive report
    final report = {
      'test_metadata': {
        'test_start_time': _testStartTime.toIso8601String(),
        'test_end_time': testEndTime.toIso8601String(),
        'total_test_duration_ms': totalTestDuration.inMilliseconds,
        'test_text': TEST_TEXT,
        'test_text_length': TEST_TEXT.length,
        'websocket_url': WEBSOCKET_URL,
        'audio_system_enabled': _audioInitialized,
        'audio_strategy': finalAudioMetrics['strategy']?.toString(),
      },
      'timing_summary': {
        'streaming_duration_ms': streamingDuration.inMilliseconds,
        'time_to_first_frame_ms':
            _firstFrameTime?.difference(_testStartTime).inMilliseconds,
        'frames_received': _framesReceived,
        'total_bytes_received': _totalBytes,
        'expected_frames': expectedFrames,
        'frame_delivery_rate_percent': frameDeliveryRate,
      },
      'frame_rate_analysis': {
        'average_interval_ms': avgInterval,
        'min_interval_ms': minInterval,
        'max_interval_ms': maxInterval,
        'average_fps': avgFps,
        'target_fps': 50.0, // 20ms frames = 50fps
        'fast_frames_count': fastFrames,
        'normal_frames_count': normalFrames,
        'slow_frames_count': slowFrames,
        'fast_frames_percent': _frameIntervals.isNotEmpty
            ? fastFrames / _frameIntervals.length * 100
            : 0,
        'slow_frames_percent': _frameIntervals.isNotEmpty
            ? slowFrames / _frameIntervals.length * 100
            : 0,
      },
      'audio_playback_analysis': {
        'audio_initialized': _audioInitialized,
        'final_audio_metrics': finalAudioMetrics,
        'audio_frames_played': finalAudioMetrics['frames_played'] ?? 0,
        'audio_frames_received': finalAudioMetrics['frames_received'] ?? 0,
        'audio_underrun_count': finalAudioMetrics['underrun_count'] ?? 0,
        'audio_playback_efficiency':
            finalAudioMetrics['frames_received'] != null &&
                    finalAudioMetrics['frames_received'] > 0
                ? (finalAudioMetrics['frames_played'] /
                        finalAudioMetrics['frames_received']) *
                    100
                : 0,
      },
      'performance_metrics': {
        'bytes_per_second': streamingDuration.inMilliseconds > 0
            ? (_totalBytes * 1000.0) / streamingDuration.inMilliseconds
            : 0,
        'frames_per_second': streamingDuration.inMilliseconds > 0
            ? (_framesReceived * 1000.0) / streamingDuration.inMilliseconds
            : 0,
        'average_frame_size_bytes':
            _framesReceived > 0 ? _totalBytes / _framesReceived : 0,
      },
      'detailed_logs': {
        'console_output': _consoleLog, // All console output captured
        'events': _eventLog,
        'frames': _frameLog,
        'frame_intervals': _frameIntervals,
      }
    };

    // Write report to file
    final file = File(OUTPUT_FILE);
    final jsonString = JsonEncoder.withIndent('  ').convert(report);
    await file.writeAsString(jsonString);

    _logPrint('📄 Test report saved to: $OUTPUT_FILE');

    // Print summary to console
    _printSummary(report);
  }

  /// Print test summary to console
  void _printSummary(Map<String, dynamic> report) {
    final separator = '=' * 70;
    _logPrint('\n' + separator);
    _logPrint('🎯 CARTESIA AUDIO STREAMING TEST RESULTS WITH LIVE PLAYBACK');
    _logPrint(separator);

    final timing = report['timing_summary'];
    final frameRate = report['frame_rate_analysis'];
    final performance = report['performance_metrics'];
    final audioAnalysis = report['audio_playback_analysis'];

    _logPrint('📊 Overall Performance:');
    _logPrint('  • Frames Received: ${timing['frames_received']}');
    _logPrint('  • Total Duration: ${timing['streaming_duration_ms']}ms');
    _logPrint('  • Time to First Frame: ${timing['time_to_first_frame_ms']}ms');
    _logPrint(
        '  • Frame Delivery Rate: ${timing['frame_delivery_rate_percent'].toStringAsFixed(1)}%');

    _logPrint('\n🕒 Frame Timing Analysis:');
    _logPrint(
        '  • Average FPS: ${frameRate['average_fps'].toStringAsFixed(1)} (target: 50.0)');
    _logPrint(
        '  • Average Interval: ${frameRate['average_interval_ms'].toStringAsFixed(1)}ms (target: 20ms)');
    _logPrint(
        '  • Min/Max Interval: ${frameRate['min_interval_ms'].toStringAsFixed(1)}ms / ${frameRate['max_interval_ms'].toStringAsFixed(1)}ms');
    _logPrint(
        '  • Fast Frames (<15ms): ${frameRate['fast_frames_count']} (${frameRate['fast_frames_percent'].toStringAsFixed(1)}%)');
    _logPrint(
        '  • Normal Frames (15-25ms): ${frameRate['normal_frames_count']}');
    _logPrint(
        '  • Slow Frames (>25ms): ${frameRate['slow_frames_count']} (${frameRate['slow_frames_percent'].toStringAsFixed(1)}%)');

    _logPrint('\n🎵 Audio Playback Analysis:');
    _logPrint(
        '  • Audio System: ${audioAnalysis['audio_initialized'] ? "✅ Initialized" : "❌ Failed"}');
    _logPrint('  • Frames Played: ${audioAnalysis['audio_frames_played']}');
    _logPrint('  • Audio Underruns: ${audioAnalysis['audio_underrun_count']}');
    _logPrint(
        '  • Playback Efficiency: ${audioAnalysis['audio_playback_efficiency'].toStringAsFixed(1)}%');
    _logPrint(
        '  • Audio Strategy: ${audioAnalysis['final_audio_metrics']['strategy'] ?? 'Unknown'}');

    _logPrint('\n📈 Data Transfer:');
    _logPrint('  • Total Bytes: ${timing['total_bytes_received']}');
    _logPrint(
        '  • Bytes/Second: ${performance['bytes_per_second'].toStringAsFixed(0)}');
    _logPrint(
        '  • Average Frame Size: ${performance['average_frame_size_bytes'].toStringAsFixed(0)} bytes');

    _logPrint(
        '\n📄 Complete logs (including all console output) saved to: $OUTPUT_FILE');
    _logPrint(separator);
  }

  /// Log an event with timestamp
  void _logEvent(String eventType, Map<String, dynamic> data) {
    _eventLog.add({
      'event_type': eventType,
      'timestamp': DateTime.now().toIso8601String(),
      'relative_time_ms':
          DateTime.now().difference(_testStartTime).inMilliseconds,
      'data': data,
    });
  }

  /// Cleanup resources
  Future<void> _cleanup() async {
    _logPrint('🧹 Cleaning up...');

    // Stop audio service
    if (_audioService != null) {
      try {
        await _audioService!.stopStreaming();
        await _audioService!.dispose();
        _logPrint('🎵 Audio service stopped and disposed');
      } catch (e) {
        _logPrint('⚠️ Error stopping audio service: $e', level: 'WARNING');
      }
    }

    // Disconnect WebSocket
    if (_socket != null) {
      _socket!.disconnect();
      _socket!.dispose();
      _logPrint('🔌 WebSocket disconnected');
    }

    _logPrint('✅ Test completed and cleaned up');
  }
}

/// Main function to run the test
Future<void> main() async {
  final test = AudioStreamingTest();
  await test.runTest();
}
