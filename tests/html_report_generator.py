#!/usr/bin/env python3
"""
HTML Report Generator for Test Results
Creates comprehensive HTML reports with inputs, outputs, and media files
"""

import os
import base64
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class HTMLReportGenerator:
    """Generate comprehensive HTML reports for test scenarios"""
    
    def __init__(self, test_name: str, output_dir: str = None):
        self.test_name = test_name
        
        # Determine correct output directory based on current working directory
        if output_dir is None:
            # If we're in the project root, use tests/reports
            # If we're in the tests directory, use reports
            current_dir = os.getcwd()
            if current_dir.endswith('tests'):
                self.output_dir = "reports"
            else:
                self.output_dir = "tests/reports"
        else:
            self.output_dir = output_dir
            
        self.test_results = []
        self.start_time = datetime.now()
        self.config_info = self._get_config_info()
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _get_config_info(self) -> Dict[str, str]:
        """Get current configuration information"""
        try:
            # Import config here to avoid circular imports
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from AIPlaygroundCode.config import get_model_config, is_configured
            
            if is_configured():
                config = get_model_config()
                return {
                    'model': config.model or 'Not configured',
                    'endpoint': config.endpoint or 'Not configured',
                    'max_tokens': str(config.max_tokens) if hasattr(config, 'max_tokens') else 'Default',
                    'temperature': str(config.temperature) if hasattr(config, 'temperature') else 'Default',
                    'configured': 'Yes'
                }
            else:
                return {
                    'model': 'Not configured',
                    'endpoint': 'Not configured', 
                    'max_tokens': 'Default',
                    'temperature': 'Default',
                    'configured': 'No'
                }
        except Exception as e:
            return {
                'model': f'Error: {e}',
                'endpoint': f'Error: {e}',
                'max_tokens': 'Error',
                'temperature': 'Error', 
                'configured': 'Error'
            }
    
    def add_test_result(self, 
                       scenario: str, 
                       input_data: Dict[str, Any], 
                       output_data: str, 
                       status: str,
                       duration: float,
                       environment: str = "local",
                       media_files: Optional[List[str]] = None,
                       response_code: int = 200):
        """Add a test result to the report"""
        
        # Enhanced status evaluation for audio transcription tests
        enhanced_status = self._evaluate_audio_result(output_data, status) if self._is_audio_test(scenario) else status
        
        result = {
            'scenario': scenario,
            'input_data': input_data,
            'output_data': output_data,
            'status': enhanced_status,
            'duration': duration,
            'environment': environment,
            'media_files': media_files or [],
            'response_code': response_code,
            'timestamp': datetime.now().isoformat(),
            'has_transcription': self._has_transcription_content(output_data)
        }
        
        self.test_results.append(result)
    
    def encode_media_file(self, file_path: str) -> Optional[Dict[str, str]]:
        """Encode media file to base64 for embedding in HTML"""
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                file_extension = os.path.splitext(file_path)[1].lower()
                
                if file_extension in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                elif file_extension == '.png':
                    mime_type = 'image/png'
                elif file_extension == '.mp3':
                    mime_type = 'audio/mpeg'
                elif file_extension == '.wav':
                    mime_type = 'audio/wav'
                else:
                    mime_type = 'application/octet-stream'
                
                encoded_data = base64.b64encode(file_data).decode('utf-8')
                
                return {
                    'filename': os.path.basename(file_path),
                    'mime_type': mime_type,
                    'data': encoded_data,
                    'size': len(file_data)
                }
        except Exception as e:
            print(f"Error encoding file {file_path}: {e}")
            return None
    
    def generate_html_report(self) -> str:
        """Generate comprehensive HTML report"""
        
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate statistics
        passed_tests = sum(1 for result in self.test_results if result['status'] == 'PASSED')
        partial_tests = sum(1 for result in self.test_results if result['status'] == 'PARTIAL')
        failed_tests = sum(1 for result in self.test_results if result['status'] == 'FAILED')
        success_rate = (passed_tests / len(self.test_results) * 100) if self.test_results else 0
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.test_name} - Test Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #007acc;
        }}
        .header h1 {{
            color: #007acc;
            margin: 0;
            font-size: 2.5em;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 1.2em;
            margin-top: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e9ecef;
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #007acc;
        }}
        .stat-card.success .value {{ color: #28a745; }}
        .stat-card.danger .value {{ color: #dc3545; }}
        .test-result {{
            margin-bottom: 30px;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            overflow: hidden;
        }}
        .result-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
        }}
        .result-header:hover {{
            background: #e9ecef;
        }}
        .result-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #495057;
        }}
        .status-badge {{
            padding: 5px 15px;
            border-radius: 15px;
            color: white;
            font-size: 0.9em;
            font-weight: bold;
        }}
        .status-badge.passed {{ background: #28a745; }}
        .status-badge.failed {{ background: #dc3545; }}
        .status-badge.partial {{ background: #fd7e14; }}
        .result-content {{
            padding: 20px;
            display: none;
        }}
        .result-content.expanded {{
            display: block;
        }}
        .input-section, .output-section, .media-section {{
            margin-bottom: 20px;
        }}
        .section-title {{
            font-size: 1.1em;
            font-weight: bold;
            color: #007acc;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid #007acc;
        }}
        .input-data {{
            background: #f1f3f4;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            border-left: 4px solid #007acc;
        }}
        .output-data {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #28a745;
            max-height: 400px;
            overflow-y: auto;
        }}
        .media-item {{
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }}
        .media-item img {{
            max-width: 300px;
            max-height: 200px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .media-item audio {{
            width: 100%;
            margin-top: 10px;
        }}
        .meta-info {{
            display: flex;
            gap: 20px;
            margin-top: 15px;
            font-size: 0.9em;
            color: #666;
        }}
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .toggle-btn {{
            background: none;
            border: none;
            font-size: 1.2em;
            cursor: pointer;
            color: #007acc;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
    <script>
        function toggleResult(index) {{
            const content = document.getElementById('result-content-' + index);
            const btn = document.getElementById('toggle-btn-' + index);
            
            if (content.classList.contains('expanded')) {{
                content.classList.remove('expanded');
                btn.textContent = '▶';
            }} else {{
                content.classList.add('expanded');
                btn.textContent = '▼';
            }}
        }}
        
        function expandAll() {{
            const contents = document.querySelectorAll('.result-content');
            const buttons = document.querySelectorAll('.toggle-btn');
            
            contents.forEach(content => content.classList.add('expanded'));
            buttons.forEach(btn => btn.textContent = '▼');
        }}
        
        function collapseAll() {{
            const contents = document.querySelectorAll('.result-content');
            const buttons = document.querySelectorAll('.toggle-btn');
            
            contents.forEach(content => content.classList.remove('expanded'));
            buttons.forEach(btn => btn.textContent = '▶');
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 {self.test_name}</h1>
            <div class="subtitle">Zava AI Chatbot Test Report</div>
            <div class="subtitle">Generated on {end_time.strftime('%Y-%m-%d at %H:%M:%S')}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>🤖 AI Model</h3>
                <div class="value" style="font-size: 1.2em; color: #007acc;">{self.config_info['model']}</div>
            </div>
            <div class="stat-card">
                <h3>🌐 Endpoint</h3>
                <div class="value" style="font-size: 0.8em; color: #495057; word-break: break-all;">
                    {self.config_info['endpoint'][:40] + '...' if len(self.config_info['endpoint']) > 40 else self.config_info['endpoint']}
                </div>
            </div>
            <div class="stat-card">
                <h3>⚙️ Max Tokens</h3>
                <div class="value" style="font-size: 1.5em;">{self.config_info['max_tokens']}</div>
            </div>
            <div class="stat-card">
                <h3>🌡️ Temperature</h3>
                <div class="value" style="font-size: 1.5em;">{self.config_info['temperature']}</div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Tests</h3>
                <div class="value">{len(self.test_results)}</div>
            </div>
            <div class="stat-card success">
                <h3>Passed</h3>
                <div class="value">{passed_tests}</div>
            </div>
            <div class="stat-card" style="background: #fff3cd;">
                <h3>Partial</h3>
                <div class="value" style="color: #fd7e14;">{partial_tests}</div>
            </div>
            <div class="stat-card danger">
                <h3>Failed</h3>
                <div class="value">{failed_tests}</div>
            </div>
            <div class="stat-card">
                <h3>Success Rate</h3>
                <div class="value">{success_rate:.1f}%</div>
            </div>
            <div class="stat-card">
                <h3>Duration</h3>
                <div class="value">{total_duration:.1f}s</div>
            </div>
        </div>
        
        <div style="text-align: center; margin-bottom: 20px;">
            <button onclick="expandAll()" style="margin-right: 10px; padding: 10px 20px; background: #007acc; color: white; border: none; border-radius: 5px; cursor: pointer;">Expand All</button>
            <button onclick="collapseAll()" style="padding: 10px 20px; background: #6c757d; color: white; border: none; border-radius: 5px; cursor: pointer;">Collapse All</button>
        </div>
        """
        
        # Add test results
        for i, result in enumerate(self.test_results):
            if result['status'] == 'PASSED':
                status_class = 'passed'
            elif result['status'] == 'PARTIAL':
                status_class = 'partial'
            else:
                status_class = 'failed'
            
            html_content += f"""
        <div class="test-result">
            <div class="result-header" onclick="toggleResult({i})">
                <div class="result-title">
                    {result['scenario']} - {result['environment'].upper()}
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span class="status-badge {status_class}">{result['status']}</span>
                    <button id="toggle-btn-{i}" class="toggle-btn">▶</button>
                </div>
            </div>
            <div id="result-content-{i}" class="result-content">
                <div class="input-section">
                    <div class="section-title">📝 Test Input</div>
                    <div class="input-data">{json.dumps(result['input_data'], indent=2)}</div>
                </div>
            """
            
            # Add media files if any
            if result['media_files']:
                html_content += f"""
                <div class="media-section">
                    <div class="section-title">📎 Media Files</div>
                """
                
                for media_file in result['media_files']:
                    encoded_media = self.encode_media_file(media_file)
                    if encoded_media:
                        if encoded_media['mime_type'].startswith('image/'):
                            html_content += f"""
                    <div class="media-item">
                        <strong>📷 {encoded_media['filename']}</strong> ({encoded_media['size']:,} bytes)
                        <br>
                        <img src="data:{encoded_media['mime_type']};base64,{encoded_media['data']}" 
                             alt="{encoded_media['filename']}" 
                             title="{encoded_media['filename']}">
                    </div>
                            """
                        elif encoded_media['mime_type'].startswith('audio/'):
                            html_content += f"""
                    <div class="media-item">
                        <strong>🎵 {encoded_media['filename']}</strong> ({encoded_media['size']:,} bytes)
                        <br>
                        <audio controls>
                            <source src="data:{encoded_media['mime_type']};base64,{encoded_media['data']}" 
                                    type="{encoded_media['mime_type']}">
                            Your browser does not support the audio element.
                        </audio>
                    </div>
                            """
                
                html_content += "</div>"
            
            html_content += f"""
                <div class="output-section">
                    <div class="section-title">💬 AI Response</div>
                    <div class="output-data">{self._format_text_for_html(result['output_data'])}</div>
                </div>
                
                <div class="meta-info">
                    <div class="meta-item">⏱️ Duration: {result['duration']:.2f}s</div>
                    <div class="meta-item">🌐 Environment: {result['environment']}</div>
                    <div class="meta-item">📊 Status Code: {result['response_code']}</div>
                    <div class="meta-item">⏰ Time: {datetime.fromisoformat(result['timestamp']).strftime('%H:%M:%S')}</div>
                </div>
            </div>
        </div>
            """
        
        html_content += f"""
        <div class="footer">
            <p>Report generated by Zava AI Chatbot Test Suite</p>
            <p>Total execution time: {total_duration:.2f} seconds</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_content
    
    def _format_text_for_html(self, text: str) -> str:
        """Format text for HTML display, preserving analysis sections with proper styling"""
        import html
        
        # Escape HTML characters
        escaped_text = html.escape(text)
        
        # Convert newlines to <br> tags
        formatted_text = escaped_text.replace('\n', '<br>')
        
        # Style analysis sections
        if '[RELEVANCE ANALYSIS]' in formatted_text:
            formatted_text = formatted_text.replace(
                '[RELEVANCE ANALYSIS]',
                '<div style="margin-top:15px;padding:10px;background:#e8f4fd;border-left:4px solid #007acc;border-radius:5px;"><strong style="color:#007acc;">📊 RELEVANCE ANALYSIS</strong></div><div style="margin-top:5px;font-family:monospace;font-size:0.9em;">'
            )
            # Close the analysis div before any other section
            formatted_text = formatted_text.replace('</div><div style="margin-top:5px;font-family:monospace;font-size:0.9em;">', '</div><div style="margin-top:5px;font-family:monospace;font-size:0.9em;margin-bottom:10px;">')
            
        if '[AUDIO ANALYSIS]' in formatted_text:
            formatted_text = formatted_text.replace(
                '[AUDIO ANALYSIS]',
                '<div style="margin-top:15px;padding:10px;background:#e8f4fd;border-left:4px solid #007acc;border-radius:5px;"><strong style="color:#007acc;">🎵 AUDIO ANALYSIS</strong></div><div style="margin-top:5px;font-family:monospace;font-size:0.9em;margin-bottom:10px;">'
            )
        
        # Highlight transcription content
        if '**📝 transcription:**' in formatted_text.lower() or 'transcription:' in formatted_text.lower():
            formatted_text = formatted_text.replace(
                '**📝 Transcription:**',
                '<div style="margin-top:10px;padding:10px;background:#f0f8f0;border-left:4px solid #28a745;border-radius:5px;"><strong style="color:#28a745;">📝 TRANSCRIPTION CONTENT</strong></div><div style="margin-top:5px;font-family:Georgia,serif;font-size:0.95em;line-height:1.5;background:#fafafa;padding:10px;border-radius:5px;">'
            )
            
        # Highlight audio processing indicators
        success_patterns = [
            ('✅ AUDIO TRANSCRIPTION WORKING!', '<span style="background:#d4edda;color:#155724;padding:3px 6px;border-radius:3px;font-weight:bold;">✅ AUDIO TRANSCRIPTION WORKING!</span>'),
            ('🎤 **Audio Processing Complete**', '<span style="background:#d4edda;color:#155724;padding:3px 6px;border-radius:3px;font-weight:bold;">🎤 Audio Processing Complete</span>')
        ]
        
        for pattern, replacement in success_patterns:
            if pattern in formatted_text:
                formatted_text = formatted_text.replace(pattern, replacement)
            
        # Style bullet points
        formatted_text = formatted_text.replace('• ', '<span style="color:#007acc;font-weight:bold;">• </span>')
        
        # Close any open analysis divs at the end
        if '[RELEVANCE ANALYSIS]' in text or '[AUDIO ANALYSIS]' in text:
            formatted_text += '</div>'
            
        return formatted_text
    
    def save_report(self, filename: Optional[str] = None) -> str:
        """Save the HTML report to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.test_name.lower().replace(' ', '_')}_{timestamp}.html"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate_html_report())
        
        return filepath
    
    def _is_audio_test(self, scenario: str) -> bool:
        """Check if this is an audio-related test scenario"""
        audio_keywords = ['audio', 'transcribe', 'customer support', 'call', 'recording']
        return any(keyword.lower() in scenario.lower() for keyword in audio_keywords)
    
    def _has_transcription_content(self, output_data: str) -> bool:
        """Check if the output contains actual transcription content"""
        transcription_indicators = [
            'transcription:', '**transcription:**', 'transcript:', 
            'customer said', 'representative said', 'caller:', 'agent:',
            'hello', 'thank you', 'how can i help', 'i would like to',
            'audio processing complete', '🎤', 'audio file received'
        ]
        output_lower = output_data.lower()
        return any(indicator in output_lower for indicator in transcription_indicators)
    
    def _evaluate_audio_result(self, output_data: str, original_status: str) -> str:
        """Enhanced evaluation for audio test results"""
        output_lower = output_data.lower()
        
        # Check for clear success indicators
        success_indicators = [
            '✅ audio transcription working!',
            'audio processing complete',
            'transcription:',
            '**transcription:**'
        ]
        
        # Check for clear failure indicators
        failure_indicators = [
            '❌',
            'error:',
            'failed to',
            'no transcription',
            'audio model not available',
            'fallback response'
        ]
        
        # Check for partial success indicators
        partial_indicators = [
            '⚠️ partial transcription detected',
            '⚠️ ai processing detected',
            'audio file received',
            'current model supports text and image'
        ]
        
        has_success = any(indicator in output_lower for indicator in success_indicators)
        has_failure = any(indicator in output_lower for indicator in failure_indicators)
        has_partial = any(indicator in output_lower for indicator in partial_indicators)
        has_transcription = self._has_transcription_content(output_data)
        
        # Enhanced decision logic
        if has_success and has_transcription:
            return "PASSED"
        elif has_success and not has_transcription:
            return "PARTIAL"  # Claims success but no actual transcription
        elif has_failure:
            return "FAILED"
        elif has_partial or (has_transcription and not has_failure):
            return "PARTIAL"
        else:
            return original_status