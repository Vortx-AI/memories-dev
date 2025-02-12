from typing import Dict, Any, Optional
import numpy as np
from Py6S import SixS, AtmosProfile, AeroProfile, Geometry
from datetime import datetime
import os
import subprocess
from pathlib import Path

class AtmosphericCorrection:
    """Atmospheric correction using Py6S and libRadtran."""
    
    def __init__(
        self,
        use_libradtran: bool = False,
        libradtran_path: Optional[Path] = None
    ):
        self.use_libradtran = use_libradtran
        self.libradtran_path = libradtran_path
        self.sixs = SixS()
        
    def correct_image(
        self,
        data: np.ndarray,
        metadata: Dict[str, Any],
        coordinates: tuple,
        timestamp: datetime
    ) -> np.ndarray:
        """Apply atmospheric correction to satellite imagery."""
        if self.use_libradtran and self.libradtran_path:
            return self._correct_libradtran(data, metadata, coordinates, timestamp)
        else:
            return self._correct_sixs(data, metadata, coordinates, timestamp)
    
    def _correct_sixs(
        self,
        data: np.ndarray,
        metadata: Dict[str, Any],
        coordinates: tuple,
        timestamp: datetime
    ) -> np.ndarray:
        """Atmospheric correction using 6S (Second Simulation of Satellite Signal in the Solar Spectrum)."""
        # Set geometry
        lat, lon = coordinates
        self.sixs.geometry = Geometry.User()
        self.sixs.geometry.view_z = metadata.get("view_zenith", 0)
        self.sixs.geometry.view_a = metadata.get("view_azimuth", 0)
        self.sixs.geometry.month = timestamp.month
        self.sixs.geometry.day = timestamp.day
        self.sixs.geometry.gmt_decimal_hour = timestamp.hour + timestamp.minute / 60.0
        self.sixs.geometry.latitude = lat
        self.sixs.geometry.longitude = lon
        
        # Set atmospheric profile
        self.sixs.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.MidlatitudeSummer)
        
        # Set aerosol profile
        self.sixs.aero_profile = AeroProfile.PredefinedType(AeroProfile.Maritime)
        
        # Process each band
        corrected_data = np.zeros_like(data, dtype=np.float32)
        for i in range(data.shape[0]):  # For each band
            # Set wavelength for current band
            wavelength = metadata.get(f"wavelength_{i}", 0.5)  # Default to 500nm
            self.sixs.wavelength = wavelength
            
            # Run 6S
            self.sixs.run()
            
            # Apply correction
            xa = self.sixs.outputs.coef_xa
            xb = self.sixs.outputs.coef_xb
            xc = self.sixs.outputs.coef_xc
            
            # Apply correction factors
            corrected = (xa * data[i] - xb) / (1 + xc * data[i])
            corrected_data[i] = corrected
            
        return corrected_data
    
    def _correct_libradtran(
        self,
        data: np.ndarray,
        metadata: Dict[str, Any],
        coordinates: tuple,
        timestamp: datetime
    ) -> np.ndarray:
        """Atmospheric correction using libRadtran."""
        if not self.libradtran_path:
            raise ValueError("libRadtran path not set")
            
        # Create input file
        input_file = self._create_libradtran_input(metadata, coordinates, timestamp)
        
        # Process each band
        corrected_data = np.zeros_like(data, dtype=np.float32)
        for i in range(data.shape[0]):
            # Update wavelength in input file
            wavelength = metadata.get(f"wavelength_{i}", 0.5)
            self._update_wavelength(input_file, wavelength)
            
            # Run libRadtran
            output = self._run_libradtran(input_file)
            
            # Parse results and apply correction
            correction_factors = self._parse_libradtran_output(output)
            corrected_data[i] = self._apply_libradtran_correction(
                data[i],
                correction_factors
            )
            
        return corrected_data
    
    def _create_libradtran_input(
        self,
        metadata: Dict[str, Any],
        coordinates: tuple,
        timestamp: datetime
    ) -> Path:
        """Create libRadtran input file."""
        lat, lon = coordinates
        input_path = Path("libradtran_input.inp")
        
        with open(input_path, "w") as f:
            f.write("atmosphere_file ../data/atmmod/afglms.dat\n")
            f.write(f"latitude {lat}\n")
            f.write(f"longitude {lon}\n")
            f.write(f"time {timestamp.strftime('%Y %m %d %H %M')}\n")
            f.write("aerosol_default\n")
            f.write("source solar\n")
            f.write("albedo 0.2\n")
            f.write("rte_solver disort\n")
            
        return input_path
    
    def _update_wavelength(self, input_file: Path, wavelength: float):
        """Update wavelength in libRadtran input file."""
        with open(input_file, "a") as f:
            f.write(f"wavelength {wavelength*1000:.1f}\n")  # Convert to nm
    
    def _run_libradtran(self, input_file: Path) -> str:
        """Run libRadtran and return output."""
        result = subprocess.run(
            [str(self.libradtran_path / "bin" / "uvspec")],
            input=input_file.read_text(),
            text=True,
            capture_output=True
        )
        return result.stdout
    
    def _parse_libradtran_output(self, output: str) -> Dict[str, float]:
        """Parse libRadtran output to get correction factors."""
        lines = output.strip().split("\n")
        values = [float(x) for x in lines[-1].split()]
        
        return {
            "direct_transmittance": values[1],
            "diffuse_transmittance": values[2],
            "total_transmittance": values[3]
        }
    
    def _apply_libradtran_correction(
        self,
        data: np.ndarray,
        factors: Dict[str, float]
    ) -> np.ndarray:
        """Apply libRadtran correction factors."""
        # Simple correction using total transmittance
        return data / factors["total_transmittance"] 