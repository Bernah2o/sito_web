"""
Firebase Storage utilities for DH2OCOL application
Handles file uploads, downloads, and management operations
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import firebase_admin
from firebase_admin import credentials, storage
from werkzeug.datastructures import FileStorage
from PIL import Image
import io

class FirebaseStorageManager:
    """Manages Firebase Storage operations for the application"""
    
    def __init__(self):
        self.bucket = None
        self.initialized = False
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if we're in development mode without Firebase
            if os.getenv('FLASK_ENV') == 'development' and not os.getenv('FIREBASE_PROJECT_ID'):
                print("Running in development mode without Firebase - Firebase Storage disabled")
                self.initialized = False
                return
            
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Get Firebase credentials from environment variables
                firebase_config = {
                    "type": os.getenv('FIREBASE_TYPE'),
                    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                    "private_key": os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
                    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                    "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
                    "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
                    "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
                    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
                    "universe_domain": os.getenv('FIREBASE_UNIVERSE_DOMAIN', 'googleapis.com')
                }
                
                # Validate required fields
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if not firebase_config.get(field)]
                
                if missing_fields:
                    print(f"Firebase configuration incomplete: {', '.join(missing_fields)}")
                    print("Running without Firebase Storage - uploads will be disabled")
                    self.initialized = False
                    return
                
                # Initialize Firebase
                cred = credentials.Certificate(firebase_config)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': f"{firebase_config['project_id']}.appspot.com"
                })
            
            # Get storage bucket
            self.bucket = storage.bucket()
            self.initialized = True
            print("Firebase Storage initialized successfully")
            
        except Exception as e:
            print(f"Error initializing Firebase Storage: {str(e)}")
            print("Running without Firebase Storage - uploads will be disabled")
            self.initialized = False
    
    def is_initialized(self) -> bool:
        """Check if Firebase Storage is properly initialized"""
        return self.initialized and self.bucket is not None
    
    def _generate_unique_filename(self, original_filename: str, folder: str = "") -> str:
        """Generate a unique filename to avoid conflicts"""
        # Get file extension
        name, ext = os.path.splitext(original_filename)
        
        # Generate unique identifier
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create unique filename
        unique_filename = f"{name}_{timestamp}_{unique_id}{ext}"
        
        # Add folder prefix if specified
        if folder:
            unique_filename = f"{folder}/{unique_filename}"
        
        return unique_filename
    
    def _optimize_image(self, file_data: bytes, max_size: Tuple[int, int] = (500, 375), quality: int = 90) -> bytes:
        """Optimize image for web usage with better sizing for product cards"""
        try:
            # Open image
            image = Image.open(io.BytesIO(file_data))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Correct orientation based on EXIF data
            from PIL import ImageOps
            image = ImageOps.exif_transpose(image)
            
            # Calculate optimal size maintaining aspect ratio
            original_width, original_height = image.size
            target_width, target_height = max_size
            
            # Calculate scaling factor to fit within target size
            scale_factor = min(target_width / original_width, target_height / original_height)
            
            if scale_factor < 1:  # Only resize if image is larger than target
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create final image with white background centered
            final_image = Image.new('RGB', max_size, (255, 255, 255))
            x_offset = (max_size[0] - image.width) // 2
            y_offset = (max_size[1] - image.height) // 2
            final_image.paste(image, (x_offset, y_offset))
            
            # Save optimized image
            output = io.BytesIO()
            final_image.save(output, format='JPEG', quality=quality, optimize=True)
            
            return output.getvalue()
        except Exception as e:
            print(f"Error optimizing image: {str(e)}")
            return file_data

    def _optimize_carousel_image(self, file_data: bytes, max_size: Tuple[int, int] = (1920, 1080), quality: int = 95) -> bytes:
        """Optimize image specifically for carousel usage with higher quality preservation"""
        try:
            # Open image
            image = Image.open(io.BytesIO(file_data))
            
            # Preserve original format if possible
            original_format = image.format
            
            # Correct orientation based on EXIF data first
            from PIL import ImageOps
            image = ImageOps.exif_transpose(image)
            
            # Get original dimensions
            original_width, original_height = image.size
            target_width, target_height = max_size
            
            # Only resize if image is significantly larger than target
            # Allow some tolerance to avoid unnecessary resizing
            scale_factor = min(target_width / original_width, target_height / original_height)
            
            if scale_factor < 0.8:  # Only resize if image is much larger than target
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                # Use LANCZOS for high-quality resizing
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Determine best output format
            output = io.BytesIO()
            
            # For carousel images, prefer to keep original format if it's high quality
            if original_format in ['PNG', 'WEBP'] and image.mode in ['RGBA', 'LA']:
                # Keep transparency for PNG/WEBP
                if original_format == 'PNG':
                    image.save(output, format='PNG', optimize=True, compress_level=6)
                else:
                    # Convert to RGB for JPEG with high quality
                    if image.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', image.size, (255, 255, 255))
                        if image.mode == 'P':
                            image = image.convert('RGBA')
                        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                        image = background
                    elif image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    image.save(output, format='JPEG', quality=quality, optimize=True)
            else:
                # Convert to RGB for JPEG
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Use higher quality for carousel images
                image.save(output, format='JPEG', quality=quality, optimize=True)
            
            return output.getvalue()
        except Exception as e:
            print(f"Error optimizing carousel image: {str(e)}")
            return file_data

    def _optimize_product_image_by_category(self, file_data: bytes, category: str) -> bytes:
        """Optimize product images based on their category with specific parameters"""
        try:
            # Define category-specific optimization parameters
            category_settings = {
                'Tanques': {
                    'max_size': (800, 600),
                    'quality': 92,
                    'description': 'High resolution for detailed tank views'
                },
                'Bombas': {
                    'max_size': (700, 525),
                    'quality': 90,
                    'description': 'Good detail for mechanical components'
                },
                'Filtros': {
                    'max_size': (600, 450),
                    'quality': 88,
                    'description': 'Clear view of filter systems'
                },
                'Accesorios': {
                    'max_size': (500, 375),
                    'quality': 85,
                    'description': 'Compact size for small accessories'
                },
                'Químicos': {
                    'max_size': (550, 400),
                    'quality': 87,
                    'description': 'Clear product labeling visibility'
                },
                'Herramientas': {
                    'max_size': (650, 500),
                    'quality': 89,
                    'description': 'Good detail for tool identification'
                }
            }
            
            # Get settings for the category, default to Accesorios if not found
            settings = category_settings.get(category, category_settings['Accesorios'])
            max_size = settings['max_size']
            quality = settings['quality']
            
            print(f"Optimizing {category} product image: {settings['description']} - {max_size} at {quality}% quality")
            
            # Open image
            image = Image.open(io.BytesIO(file_data))
            
            # Correct orientation based on EXIF data
            from PIL import ImageOps
            image = ImageOps.exif_transpose(image)
            
            # Convert to RGB if necessary, but preserve quality
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Calculate optimal size maintaining aspect ratio
            original_width, original_height = image.size
            target_width, target_height = max_size
            
            # Calculate scaling factor to fit within target size
            scale_factor = min(target_width / original_width, target_height / original_height)
            
            # Only resize if image is larger than target (avoid upscaling)
            if scale_factor < 1:
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                # Use LANCZOS for high-quality resizing
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # For product images, maintain aspect ratio without adding background
            # This preserves the natural proportions of the product
            
            # Save optimized image
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            
            return output.getvalue()
        except Exception as e:
            print(f"Error optimizing {category} product image: {str(e)}")
            return file_data
    
    def upload_file(self, file: FileStorage, folder: str = "", optimize_image: bool = True, product_category: str = None) -> Optional[str]:
        """
        Upload a file to Firebase Storage
        
        Args:
            file: FileStorage object from Flask
            folder: Folder path in storage (e.g., 'productos', 'servicios', 'carousel')
            optimize_image: Whether to optimize images before upload
            product_category: Product category for category-specific optimization (Tanques, Bombas, etc.)
        
        Returns:
            Public URL of uploaded file or None if failed
        """
        if not self.is_initialized():
            print("Firebase Storage not initialized")
            return None

        if not file or not file.filename:
            print("No file provided")
            return None

        print(f"Firebase: Uploading file {file.filename} to folder '{folder}'")
        print(f"Firebase: Content type: {file.content_type}")
        print(f"Firebase: Product category: {product_category}")

        try:
            # Generate unique filename
            filename = self._generate_unique_filename(file.filename, folder)
            print(f"Firebase: Generated filename: {filename}")
            
            # Read file data
            file_data = file.read()
            print(f"Firebase: File data size: {len(file_data)} bytes")
            
            if len(file_data) == 0:
                print("Firebase: Error - File data is empty")
                return None
            
            # Validate image format if it's supposed to be an image
            if file.content_type and file.content_type.startswith('image/'):
                try:
                    # Try to open the image to validate it
                    img = Image.open(io.BytesIO(file_data))
                    img.verify()  # Verify that it's a valid image
                    print(f"Firebase: Image validation successful - Format: {img.format}, Size: {img.size}")
                except Exception as img_error:
                    print(f"Firebase: Image validation failed: {img_error}")
                    return None
            
            # Optimize image if it's an image file and optimization is enabled
            if optimize_image and file.content_type and file.content_type.startswith('image/'):
                # Use specific optimization based on folder/purpose
                if folder == 'carousel':
                    # Use high-quality optimization for carousel images
                    file_data = self._optimize_carousel_image(file_data)
                    print(f"Firebase: Optimizing carousel image with high quality settings")
                elif folder == 'productos' and product_category:
                    # Use category-specific optimization for product images
                    file_data = self._optimize_product_image_by_category(file_data, product_category)
                    print(f"Firebase: Optimizing product image for category: {product_category}")
                else:
                    # Use standard optimization for other images (services, general, etc.)
                    file_data = self._optimize_image(file_data)
                    print(f"Firebase: Optimizing image with standard settings for folder: {folder}")
                
                print(f"Firebase: Optimized file data size: {len(file_data)} bytes")
            
            # Upload to Firebase Storage
            blob = self.bucket.blob(filename)
            blob.upload_from_string(file_data, content_type=file.content_type)
            # Add long-lived caching for static media assets
            blob.cache_control = "public, max-age=31536000, immutable"
            try:
                blob.patch()
            except Exception:
                pass
            print(f"Firebase: File uploaded successfully")
            
            # Make the file publicly accessible
            blob.make_public()
            print(f"Firebase: File made public")
            
            # Return public URL
            public_url = blob.public_url
            print(f"Firebase: Public URL: {public_url}")
            return public_url
            
        except Exception as e:
            print(f"Firebase: Error uploading file: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete a file from Firebase Storage using its public URL
        
        Args:
            file_url: Public URL of the file to delete
        
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.is_initialized():
            return False
        
        try:
            # Support both public URL formats
            # 1) https://storage.googleapis.com/<bucket>/<object_path>
            # 2) https://firebasestorage.googleapis.com/v0/b/<bucket>/o/<object_path>?...
            import urllib.parse
            parsed = urllib.parse.urlparse(file_url)
            blob_name = None

            if 'storage.googleapis.com' in file_url:
                # Path: /<bucket>/<object_path>
                path = parsed.path.lstrip('/')
                parts = path.split('/', 1)
                if len(parts) == 2:
                    blob_name = urllib.parse.unquote(parts[1])
                else:
                    # Fallback if object path not found
                    blob_name = urllib.parse.unquote(parts[0])
            elif 'firebasestorage.googleapis.com' in file_url:
                # Path: /v0/b/<bucket>/o/<object_path>
                segments = parsed.path.split('/')
                try:
                    o_index = segments.index('o')
                    blob_name = urllib.parse.unquote(segments[o_index + 1])
                except Exception:
                    # Some signed URLs may have the name in query param
                    qs = urllib.parse.parse_qs(parsed.query)
                    name = qs.get('name', [None])[0]
                    blob_name = urllib.parse.unquote(name) if name else None
            
            if not blob_name:
                print(f"Could not extract blob name from URL: {file_url}")
                return False

            # Delete the file by its full object path (may include folders like 'servicios/...')
            blob = self.bucket.blob(blob_name)
            blob.delete()
            return True
                
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
    
    def list_files(self, folder: str = "", limit: int = 100) -> List[dict]:
        """
        List files in a specific folder
        
        Args:
            folder: Folder path to list files from
            limit: Maximum number of files to return
        
        Returns:
            List of file information dictionaries
        """
        if not self.is_initialized():
            return []
        
        try:
            files = []
            blobs = self.bucket.list_blobs(prefix=folder, max_results=limit)
            
            for blob in blobs:
                files.append({
                    'name': blob.name,
                    'url': blob.public_url,
                    'size': blob.size,
                    'created': blob.time_created,
                    'updated': blob.updated,
                    'content_type': blob.content_type
                })
            
            return files
            
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return []
    
    def get_signed_url(self, filename: str, expiration_hours: int = 1) -> Optional[str]:
        """
        Generate a signed URL for private file access
        
        Args:
            filename: Name of the file in storage
            expiration_hours: Hours until the URL expires
        
        Returns:
            Signed URL or None if failed
        """
        if not self.is_initialized():
            return None
        
        try:
            blob = self.bucket.blob(filename)
            expiration = datetime.utcnow() + timedelta(hours=expiration_hours)
            
            signed_url = blob.generate_signed_url(expiration=expiration)
            return signed_url
            
        except Exception as e:
            print(f"Error generating signed URL: {str(e)}")
            return None

# Global instance
firebase_storage = FirebaseStorageManager()

# Utility functions for easy access
def upload_file(file: FileStorage, folder: str = "", optimize_image: bool = True, product_category: str = None) -> Optional[str]:
    """Upload a file to Firebase Storage"""
    return firebase_storage.upload_file(file, folder, optimize_image, product_category)

def delete_file(file_url: str) -> bool:
    """Delete a file from Firebase Storage"""
    return firebase_storage.delete_file(file_url)

def list_files(folder: str = "", limit: int = 100) -> List[dict]:
    """List files in Firebase Storage"""
    return firebase_storage.list_files(folder, limit)

def upload_file_from_path(local_file_path: str, folder: str = "", optimize_image: bool = True) -> Optional[str]:
    """
    Upload a file from local path to Firebase Storage
    
    Args:
        local_file_path: Path to the local file
        folder: Folder path in storage
        optimize_image: Whether to optimize images before upload
    
    Returns:
        Public URL of uploaded file or None if failed
    """
    if not firebase_storage.is_initialized():
        print("Firebase Storage not initialized")
        return None
    
    try:
        import mimetypes
        from pathlib import Path
        
        # Check if file exists
        if not os.path.exists(local_file_path):
            print(f"File not found: {local_file_path}")
            return None
        
        # Get file info
        file_path = Path(local_file_path)
        filename = file_path.name
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(local_file_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Generate unique filename
        unique_filename = firebase_storage._generate_unique_filename(filename, folder)
        
        # Read file data
        with open(local_file_path, 'rb') as f:
            file_data = f.read()
        
        # Optimize image if it's an image file and optimization is enabled
        if optimize_image and content_type.startswith('image/'):
            file_data = firebase_storage._optimize_image(file_data)
        
        # Upload to Firebase Storage
        blob = firebase_storage.bucket.blob(unique_filename)
        blob.upload_from_string(file_data, content_type=content_type)
        # Add long-lived caching for static media assets
        blob.cache_control = "public, max-age=31536000, immutable"
        try:
            blob.patch()
        except Exception:
            pass
        
        # Make the file publicly accessible
        blob.make_public()
        
        # Return public URL
        return blob.public_url
        
    except Exception as e:
        print(f"Error uploading file from path: {str(e)}")
        return None

def is_firebase_available() -> bool:
    """Check if Firebase Storage is available"""
    return firebase_storage.is_initialized()