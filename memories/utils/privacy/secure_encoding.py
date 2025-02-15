import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
import numpy as np
from typing import Tuple, Optional, Dict, Any
import json
from datetime import datetime, timedelta
import jwt
from PIL import Image
import io
from shapely.geometry import shape, mapping
import sys

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
src_path = os.path.join(project_root, 'src')
sys.path.append(src_path)

from privacy.geo_privacy import GeoPrivacyEncoder

class SecureImageEncoder:
    """Secure image encoding with multiple protection layers"""
    
    def __init__(self, master_key: str):
        """Initialize with master key for derivation"""
        self.master_key = master_key.encode()
        self._initialize_keys()
        self.geo_encoder = GeoPrivacyEncoder(master_key)
        
    def _initialize_keys(self):
        """Initialize encryption keys"""
        # Generate salt
        self.salt = os.urandom(16)
        
        # Key derivation function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        
        # Derive encryption key
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        self.fernet = Fernet(key)
        
    def encode_image(
        self,
        image: np.ndarray,
        metadata: Dict[str, Any],
        protection_level: str = 'high'
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Encode image with multiple protection layers
        
        Args:
            image: numpy array image
            metadata: dict of metadata
            protection_level: 'low', 'medium', or 'high'
            
        Returns:
            encoded_data: encrypted and encoded image data
            secure_metadata: encrypted metadata with access info
        """
        # 1. Image preprocessing
        if protection_level == 'high':
            # Apply reversible image transformation
            image = self._transform_image(image)
        
        # 2. Convert to bytes
        img_bytes = self._image_to_bytes(image)
        
        # 3. Encrypt
        encrypted_data = self.fernet.encrypt(img_bytes)
        
        # 4. Generate access token
        access_token = self._generate_access_token(metadata)
        
        # 5. Create secure metadata
        secure_metadata = {
            'access_token': access_token,
            'protection_level': protection_level,
            'salt': base64.b64encode(self.salt).decode(),
            'timestamp': datetime.utcnow().isoformat(),
            'checksum': hashlib.sha256(encrypted_data).hexdigest()
        }
        
        return encrypted_data, secure_metadata
        
    def decode_image(
        self,
        encrypted_data: bytes,
        secure_metadata: Dict[str, Any],
        access_token: str
    ) -> Optional[np.ndarray]:
        """
        Decode encrypted image data
        
        Args:
            encrypted_data: encrypted image bytes
            secure_metadata: metadata with access info
            access_token: valid access token
            
        Returns:
            numpy array image if successful, None if unauthorized
        """
        try:
            # 1. Verify access token
            if not self._verify_access_token(access_token, secure_metadata):
                return None
                
            # 2. Verify checksum
            if hashlib.sha256(encrypted_data).hexdigest() != secure_metadata['checksum']:
                return None
                
            # 3. Decrypt data
            img_bytes = self.fernet.decrypt(encrypted_data)
            
            # 4. Convert back to numpy array
            image = self._bytes_to_image(img_bytes)
            
            # 5. Reverse transformation if needed
            if secure_metadata['protection_level'] == 'high':
                image = self._inverse_transform_image(image)
                
            return image
            
        except Exception as e:
            print(f"Error decoding image: {str(e)}")
            return None
            
    def _transform_image(self, image: np.ndarray) -> np.ndarray:
        """Apply reversible transformation to image"""
        # Split into bit planes and shuffle
        bit_planes = [(image >> i) & 1 for i in range(8)]
        np.random.seed(int.from_bytes(self.salt[:4], 'big'))
        shuffled_indices = np.random.permutation(8)
        transformed = sum(bit_planes[i] << j for i, j in enumerate(shuffled_indices))
        return transformed
        
    def _inverse_transform_image(self, image: np.ndarray) -> np.ndarray:
        """Reverse the image transformation"""
        # Reverse bit plane shuffling
        bit_planes = [(image >> i) & 1 for i in range(8)]
        np.random.seed(int.from_bytes(self.salt[:4], 'big'))
        shuffled_indices = np.random.permutation(8)
        inverse_indices = np.zeros_like(shuffled_indices)
        inverse_indices[shuffled_indices] = np.arange(8)
        restored = sum(bit_planes[i] << j for i, j in enumerate(inverse_indices))
        return restored
        
    def _image_to_bytes(self, image: np.ndarray) -> bytes:
        """Convert numpy array to bytes"""
        img_bytes = io.BytesIO()
        Image.fromarray(image).save(img_bytes, format='PNG')
        return img_bytes.getvalue()
        
    def _bytes_to_image(self, img_bytes: bytes) -> np.ndarray:
        """Convert bytes back to numpy array"""
        return np.array(Image.open(io.BytesIO(img_bytes)))
        
    def _generate_access_token(self, metadata: Dict[str, Any]) -> str:
        """Generate JWT access token"""
        payload = {
            'metadata': metadata,
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, self.master_key, algorithm='HS256')
        
    def _verify_access_token(self, token: str, secure_metadata: Dict[str, Any]) -> bool:
        """Verify JWT access token"""
        try:
            payload = jwt.decode(token, self.master_key, algorithms=['HS256'])
            return True
        except:
            return False

    def encode_with_geo_privacy(
        self,
        image: np.ndarray,
        geometry: Any,
        metadata: Dict[str, Any],
        protection_level: str = 'high',
        layout_type: str = 'grid',
        fractal_type: Optional[str] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Encode image with geo-privacy protection
        
        Args:
            image: numpy array image
            geometry: Shapely geometry object
            metadata: dict of metadata
            protection_level: 'low', 'medium', or 'high'
            layout_type: Type of layout transformation
            fractal_type: Optional fractal transformation
            
        Returns:
            encoded_data: encrypted and encoded image data
            secure_metadata: encrypted metadata with access info
        """
        # 1. Apply geo-privacy transformation
        transformed_geom, geo_metadata = self.geo_encoder.encode_geometry(
            geometry,
            layout_type=layout_type,
            fractal_type=fractal_type,
            protection_level=protection_level
        )
        
        # 2. Apply image encoding
        encrypted_data, secure_metadata = self.encode_image(
            image,
            metadata,
            protection_level
        )
        
        # 3. Combine metadata
        secure_metadata.update({
            'geo_privacy': geo_metadata,
            'geometry': mapping(transformed_geom)
        })
        
        return encrypted_data, secure_metadata
    
    def decode_with_geo_privacy(
        self,
        encrypted_data: bytes,
        secure_metadata: Dict[str, Any],
        access_token: str
    ) -> Tuple[Optional[np.ndarray], Optional[Any]]:
        """
        Decode image and geometry with geo-privacy protection
        
        Args:
            encrypted_data: encrypted image bytes
            secure_metadata: metadata with access info
            access_token: valid access token
            
        Returns:
            tuple of (decoded image, decoded geometry) or (None, None) if unauthorized
        """
        # 1. Decode image
        image = self.decode_image(
            encrypted_data,
            secure_metadata,
            access_token
        )
        
        if image is None:
            return None, None
            
        # 2. Decode geometry
        if 'geo_privacy' in secure_metadata:
            transformed_geom = shape(secure_metadata['geometry'])
            original_geom = self.geo_encoder.decode_geometry(
                transformed_geom,
                secure_metadata['geo_privacy']
            )
            return image, original_geom
            
        return image, None

class SecureAPILayer:
    """Secure API layer with access control"""
    
    def __init__(self, master_key: str):
        self.encoder = SecureImageEncoder(master_key)
        self.api_keys = {}  # Store API keys and permissions
        
    def register_api_key(self, api_key: str, permissions: Dict[str, Any]):
        """Register new API key with permissions"""
        self.api_keys[api_key] = {
            'permissions': permissions,
            'created_at': datetime.utcnow().isoformat()
        }
        
    def validate_api_key(self, api_key: str, required_permission: str) -> bool:
        """Validate API key and check permissions"""
        if api_key not in self.api_keys:
            return False
        return required_permission in self.api_keys[api_key]['permissions']
        
    def encode_tile(
        self,
        tile_data: np.ndarray,
        tile_metadata: Dict[str, Any],
        protection_level: str = 'high'
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Encode tile data with security layers"""
        return self.encoder.encode_image(
            tile_data,
            tile_metadata,
            protection_level
        )
        
    def decode_tile(
        self,
        encrypted_data: bytes,
        secure_metadata: Dict[str, Any],
        access_token: str
    ) -> Optional[np.ndarray]:
        """Decode tile data with access validation"""
        return self.encoder.decode_image(
            encrypted_data,
            secure_metadata,
            access_token
        )

    def encode_tile_with_geo_privacy(
        self,
        tile_data: np.ndarray,
        geometry: Any,
        tile_metadata: Dict[str, Any],
        protection_level: str = 'high',
        layout_type: str = 'grid',
        fractal_type: Optional[str] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Encode tile data with geo-privacy protection"""
        return self.encoder.encode_with_geo_privacy(
            tile_data,
            geometry,
            tile_metadata,
            protection_level,
            layout_type,
            fractal_type
        )
        
    def decode_tile_with_geo_privacy(
        self,
        encrypted_data: bytes,
        secure_metadata: Dict[str, Any],
        access_token: str
    ) -> Tuple[Optional[np.ndarray], Optional[Any]]:
        """Decode tile data with geo-privacy protection"""
        return self.encoder.decode_with_geo_privacy(
            encrypted_data,
            secure_metadata,
            access_token
        )
