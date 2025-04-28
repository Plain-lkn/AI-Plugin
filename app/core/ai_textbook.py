import os
import tempfile
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT
from moviepy import VideoFileClip
import cv2
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, SystemMessage
from sklearn.cluster import KMeans
from PIL import Image
import base64
import io

class VideoSummaryPDFGenerator:
    def __init__(self, api_key=None):
        """
        Initialize the PDF generator with OpenAI API key
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Create pdf directory if it doesn't exist
        self.pdf_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'pdf')
        os.makedirs(self.pdf_dir, exist_ok=True)

        # Register Korean font
        font_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'NotoSansKR-Regular.ttf')
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Korean font file not found at: {font_path}")
            
        try:
            pdfmetrics.registerFont(TTFont('NotoSansKR', font_path))
            print("Korean font registered successfully")
        except Exception as e:
            print(f"Error registering Korean font: {e}")
            raise
        
        # Create paragraph styles with Korean font
        self.normal_style = ParagraphStyle(
            'normal',
            fontName='NotoSansKR',
            fontSize=10,
            leading=14,
            alignment=TA_LEFT
        )
        
        # Initialize Langchain chat models
        self.vision_model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=300
        )
        self.text_model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=300
        )
        
        # Initialize prompt templates
        self.vision_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""당신은 비디오 프레임을 분석하고 설명하는 AI 도우미입니다.
            - 모든 응답은 반드시 한국어로 작성해주세요.
            - 프레임에서 보이는 장면, 동작 등을 자세히 설명해주세요.
            - 설명은 자연스러운 한국어 문장으로 작성해주세요.
            - 영어로 응답하지 마세요. 반드시 한국어로만 응답해주세요."""),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        self.commentary_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""당신은 전문적인 비디오 분석가입니다.
            - 모든 분석과 코멘트는 반드시 한국어로 작성해주세요.
            - 비디오의 주요 내용, 의미, 특징 등을 분석해주세요.
            - 분석은 전문적이면서도 이해하기 쉬운 한국어로 작성해주세요.
            - 각 세그먼트의 중요성과 의미를 설명해주세요.
            - 영어로 응답하지 마세요. 반드시 한국어로만 응답해주세요."""),
            MessagesPlaceholder(variable_name="messages")
        ])
    
    def generate_pdf(self, video_path):
        """
        Generate a PDF summary of a video with timeline segments and AI commentary
        
        Args:
            video_path: Path to the video file
        
        Returns:
            tuple: (pdf_bytes, filename) - PDF content as bytes and suggested filename
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        # Extract timeline segments
        print("Analyzing video and extracting key segments...")
        segments = self._extract_timeline_segments(video_path)
        
        # Generate summaries for each segment
        print("Generating summaries for each segment...")
        summaries = self._generate_segment_summaries(segments, video_path)
        
        # Generate AI commentary
        print("Generating AI commentary...")
        ai_commentary = self._generate_ai_commentary(summaries)
        
        # Create PDF
        print("Creating PDF...")
        video_name = os.path.basename(video_path)
        pdf_filename = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{video_name}.pdf"
        
        # Create PDF in memory
        pdf_bytes = self._create_pdf(video_path, segments, summaries, ai_commentary)
        
        # Optionally save a copy in pdf directory
        pdf_path = os.path.join(self.pdf_dir, pdf_filename)
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"PDF summary generated successfully: {pdf_path}")
        return pdf_bytes, pdf_filename
    
    def _extract_timeline_segments(self, video_path, num_segments=5):
        """
        Extract key timeline segments from the video using scene detection
        """
        video = VideoFileClip(video_path)
        duration = video.duration
        
        # Extract frames at regular intervals
        frames = []
        timestamps = []
        cap = cv2.VideoCapture(video_path)
        
        # Take samples every few seconds
        sample_interval = max(1, int(duration / 30))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Calculate frame numbers to sample
        frame_numbers = [int(i * fps * sample_interval) for i in range(int(duration / sample_interval))]
        
        for frame_number in frame_numbers:
            if frame_number >= total_frames:
                break
                
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            
            if ret:
                frames.append(cv2.resize(frame, (320, 180)))
                timestamps.append(frame_number / fps)
        
        cap.release()
        
        if not frames:
            # Fallback if frame extraction failed
            segments = []
            segment_duration = duration / num_segments
            for i in range(num_segments):
                start_time = i * segment_duration
                end_time = (i + 1) * segment_duration if i < num_segments - 1 else duration
                segments.append({
                    "name": f"분할 {i+1}",
                    "start_time": start_time,
                    "end_time": end_time
                })
            return segments
        
        # Convert frames to feature vectors (using average color histograms)
        features = []
        for frame in frames:
            hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            features.append(hist)
        
        # Cluster frames to find scene changes
        n_clusters = min(num_segments, len(features))
        if n_clusters < 2:
            n_clusters = 2
            
        kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(features)
        labels = kmeans.labels_
        
        # Find scene boundaries
        scene_changes = [0]
        for i in range(1, len(labels)):
            if labels[i] != labels[i-1]:
                scene_changes.append(i)
        scene_changes.append(len(labels) - 1)
        
        # Create segments
        segments = []
        for i in range(len(scene_changes) - 1):
            start_idx = scene_changes[i]
            end_idx = scene_changes[i+1]
            start_time = timestamps[start_idx]
            end_time = timestamps[end_idx] if end_idx < len(timestamps) else duration
            
            segments.append({
                "name": f"분할 {i+1}",
                "start_time": start_time,
                "end_time": end_time
            })
        
        return segments
    
    def _generate_segment_summaries(self, segments, video_path):
        """
        Generate text summaries for each video segment
        """
        video = VideoFileClip(video_path)
        summaries = []
        
        for segment in segments:
            # Extract a frame from the middle of the segment
            mid_time = (segment["start_time"] + segment["end_time"]) / 2
            frame = video.get_frame(mid_time)
            
            # Save frame to temporary file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
                temp_filename = temp.name
                Image.fromarray(frame).save(temp_filename)
            
            # Generate description using Langchain
            try:
                with open(temp_filename, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    
                    # Create message with image
                    message = HumanMessage(content=[
                        {"type": "text", "text": "이 비디오 프레임에서 무슨 일이 일어나고 있는지 2-3문장으로 한국어로 설명해주세요. 영어로 응답하지 마세요."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ])
                    
                    # Get response from vision model
                    response = self.vision_model.invoke([message])
                    summary = response.content
            except Exception as e:
                summary = f"이 세그먼트는 {self._format_time(segment['start_time'])}부터 {self._format_time(segment['end_time'])}까지의 내용을 보여줍니다."
                print(f"Error generating summary: {e}")
            
            # Clean up temp file
            os.unlink(temp_filename)
            
            summaries.append(summary)
        
        return summaries
    
    def _generate_ai_commentary(self, summaries):
        """
        Generate AI commentary based on the video summaries
        """
        combined_summary = "\n".join(summaries)
        
        try:
            message = HumanMessage(content=f"""다음은 비디오 세그먼트 요약입니다. 이 내용을 바탕으로 비디오의 전체적인 내용, 주제, 의미 등을 분석해주세요.
            500자 이내로 짧게 요약해주세요. 모든 분석은 반드시 한국어로 작성해주세요. 영어로 응답하지 마세요.

{combined_summary}""")
            
            # Get response from text model
            response = self.text_model.invoke([message])
            commentary = response.content
        except Exception as e:
            commentary = "AI 코멘트를 생성하는 중 오류가 발생했습니다."
            print(f"Error generating AI commentary: {e}")
        
        return commentary
    
    def _create_pdf(self, video_path, segments, summaries, ai_commentary):
        """
        Create a PDF with the video segments, summaries, and AI commentary
        Returns PDF bytes
        """
        # Create PDF in memory
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Add title
        c.setFont('NotoSansKR', 16)
        c.drawCentredString(width/2, height-50, "비디오 요약 PDF")
        
        # Add date
        c.setFont('NotoSansKR', 10)
        c.drawRightString(width-50, height-70, f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Process each segment on a new page
        video = VideoFileClip(video_path)
        
        for i, (segment, summary) in enumerate(zip(segments, summaries)):
            if i > 0:  # Start a new page for each segment after the first
                c.showPage()
            
            # Set up the page
            y_position = height - 100  # Start position from top
            
            # Draw segment title (left)
            c.setFont('NotoSansKR', 14)
            c.drawString(50, y_position, f"세그먼트 {i+1}")
            
            # Draw timeline (right)
            c.setFont('NotoSansKR', 12)
            timeline = f"{self._format_time(segment['start_time'])} - {self._format_time(segment['end_time'])}"
            timeline_width = c.stringWidth(timeline, 'NotoSansKR', 12)
            c.drawString(width - 50 - timeline_width, y_position, timeline)
            
            # Extract and add thumbnail in the center
            mid_time = (segment["start_time"] + segment["end_time"]) / 2
            frame = video.get_frame(mid_time)
            
            # Save thumbnail to temp file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
                temp_filename = temp.name
                Image.fromarray(frame).save(temp_filename)
            
            # Calculate thumbnail dimensions (centered)
            thumb_width = 300  # Fixed width
            thumb_height = 225  # Maintain 4:3 ratio
            thumb_x = (width - thumb_width) / 2
            thumb_y = y_position - 40 - thumb_height
            
            # Add thumbnail to PDF
            c.drawImage(temp_filename, thumb_x, thumb_y, width=thumb_width, height=thumb_height)
            
            # Clean up temp file
            os.unlink(temp_filename)
            
            # Add summary text below the thumbnail
            summary_style = ParagraphStyle(
                'summary',
                fontName='NotoSansKR',
                fontSize=11,
                leading=16,
                wordWrap='CJK',
                alignment=TA_LEFT,
                spaceBefore=20
            )
            
            # Create Paragraph for summary
            p = Paragraph(summary, summary_style)
            available_width = width - 100  # Margins on both sides
            text_y = thumb_y - 20  # Position below thumbnail
            
            # Wrap and draw the summary
            w, h = p.wrap(available_width, text_y)  # Get required height
            p.drawOn(c, 50, text_y - h)
        
        # Add AI commentary on a new page
        c.showPage()
        c.setFont('NotoSansKR', 14)
        c.drawString(50, height-50, "AI 종합 분석")
        
        # Create commentary style
        commentary_style = ParagraphStyle(
            'commentary',
            fontName='NotoSansKR',
            fontSize=11,
            leading=16,
            wordWrap='CJK',
            alignment=TA_LEFT,
            spaceBefore=10
        )
        
        # Add AI commentary
        p = Paragraph(ai_commentary, commentary_style)
        available_width = width - 100
        w, h = p.wrap(available_width, height-100)
        p.drawOn(c, 50, height-80-h)
        
        # Save PDF
        c.save()
        
        # Get PDF bytes
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _format_time(self, seconds):
        """Format seconds as MM:SS"""
        minutes, seconds = divmod(int(seconds), 60)
        return f"{minutes:02d}:{seconds:02d}"


if __name__ == "__main__":
    # Example usage
    import base64  # Required for image encoding
    
    generator = VideoSummaryPDFGenerator()
    video_path = "./video/세무사_꿀팁.mp4"
    generator.generate_pdf(video_path)
