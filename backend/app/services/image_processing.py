import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import io
from app.core.logging import get_logger

logger = get_logger(__name__)

class ImagePreprocessor:
    @staticmethod
    def detect_blur(image_path: Path, threshold: float = 100.0) -> float:
        """
        Detects if an image is blurry using the Laplacian variance method.
        Raises ValueError if the variance is below the threshold.
        """
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError("Failed to read image for blur detection.")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        logger.info("Blur detection: Laplacian variance = %.2f (Threshold = %.2f)", variance, threshold)
        
        if variance < threshold:
            raise ValueError("Image is too blurry. Please capture or upload a clearer, sharper image.")
        
        return variance

    @staticmethod
    def strip_metadata_and_compress(image_path: Path, max_dimension: int = 2000) -> Path:
        """
        Removes EXIF metadata and resizes the image if it exceeds max_dimension.
        Saves the processed image back to disk.
        """
        try:
            with Image.open(image_path) as img:
                # Keep orientation but strip EXIF
                img_format = img.format or "JPEG"
                
                # Check dimensions
                w, h = img.size
                if w > max_dimension or h > max_dimension:
                    if w > h:
                        new_w = max_dimension
                        new_h = int(h * (max_dimension / w))
                    else:
                        new_h = max_dimension
                        new_w = int(w * (max_dimension / h))
                    
                    logger.info("Resizing image from %dx%d to %dx%d", w, h, new_w, new_h)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Save without EXIF/metadata
                img.save(image_path, format=img_format, exif=b"")
                logger.info("Metadata stripped successfully from %s", image_path.name)
        except Exception as e:
            logger.error("Failed to strip metadata/compress image: %s", str(e))
        return image_path

    @staticmethod
    def enhance_contrast_and_brightness(img: np.ndarray) -> np.ndarray:
        """
        Enhances brightness and contrast using CLAHE in LAB color space
        to avoid altering the color balance (crucial for currency verification).
        """
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        
        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        return enhanced

    @staticmethod
    def auto_crop_and_warp(image_path: Path) -> Path:
        """
        Detects the currency note in the image, removes the background,
        corrects perspective distortion, and crop/warps the note.
        """
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError("Failed to read image for crop/warp.")

        h, w = img.shape[:2]
        
        # 1. Image preprocessing for contour detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Use Otsu's thresholding or Canny
        edged = cv2.Canny(blurred, 50, 150)
        
        # 2. Find contours
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            # Fallback: Just enhance contrast
            enhanced = ImagePreprocessor.enhance_contrast_and_brightness(img)
            cv2.imwrite(str(image_path), enhanced)
            return image_path

        # Get largest contour by area
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        largest_contour = contours[0]
        
        # Check if the contour is reasonably large (e.g. > 10% of image area)
        img_area = w * h
        contour_area = cv2.contourArea(largest_contour)
        
        if contour_area < (img_area * 0.1):
            # Not large enough to be a note, fallback
            enhanced = ImagePreprocessor.enhance_contrast_and_brightness(img)
            cv2.imwrite(str(image_path), enhanced)
            return image_path

        # 3. Approximate quadrilateral contour
        peri = cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, 0.02 * peri, True)
        
        # If quadrilateral found, warp perspective
        if len(approx) == 4:
            logger.info("Quad contour found. Warping perspective.")
            pts = approx.reshape(4, 2)
            warped = ImagePreprocessor._four_point_transform(img, pts)
            enhanced = ImagePreprocessor.enhance_contrast_and_brightness(warped)
            cv2.imwrite(str(image_path), enhanced)
        else:
            logger.info("Quad contour not found. Cropping bounding rect and masking background.")
            # Mask background and crop bounding rect
            mask = np.zeros(img.shape[:2], dtype=np.uint8)
            cv2.drawContours(mask, [largest_contour], -1, 255, -1)
            
            # Apply mask to keep note and make background black
            masked_img = cv2.bitwise_and(img, img, mask=mask)
            
            # Crop to bounding rect
            x, y, bw, bh = cv2.boundingRect(largest_contour)
            cropped = masked_img[y:y+bh, x:x+bw]
            
            enhanced = ImagePreprocessor.enhance_contrast_and_brightness(cropped)
            cv2.imwrite(str(image_path), enhanced)

        return image_path

    @staticmethod
    def _four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
        """
        Orders coordinates and performs 4-point perspective warp.
        """
        # Order points: top-left, top-right, bottom-right, bottom-left
        rect = np.zeros((4, 2), dtype="float32")
        
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        (tl, tr, br, bl) = rect
        
        # Calculate new width
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        # Calculate new height
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        return warped

    @classmethod
    def preprocess(cls, image_path: Path) -> Path:
        """
        Complete preprocessing pipeline:
        1. Blur detection
        2. EXIF Metadata removal & size compression
        3. Auto crop, perspective warp, background removal, contrast enhance
        """
        cls.detect_blur(image_path)
        cls.strip_metadata_and_compress(image_path)
        cls.auto_crop_and_warp(image_path)
        return image_path
