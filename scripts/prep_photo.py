#!/usr/bin/env python3
"""
prep_photo.py — turn a raw headshot into a clean grayscale source ready for
ASCII conversion.

Steps:
  1. Key out the (green-screen) background using HSV thresholding so the
     subject is isolated. Falls back gracefully if there's no strong green
     cast — it just won't remove much.
  2. Boost local contrast with CLAHE (contrast-limited adaptive histogram
     equalization) so a flatly-lit face gets real highlights/shadows.
  3. Composite the isolated subject onto pure white so the background maps
     to the blank end of the ASCII ramp (white -> spaces).

Usage:
    python scripts/prep_photo.py source-photo.jpg
Output:
    prepped.png  (grayscale, white background, contrast-boosted)
"""
import sys
import cv2
import numpy as np


def key_out_green(bgr: np.ndarray) -> np.ndarray:
    """Return an alpha mask (0-255) where 255 = subject, 0 = green background."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    # Green-screen band. Wide enough to catch shading/wrinkles in the cloth,
    # narrow enough to leave skin/hair/clothing alone.
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    # Subject = everything that is NOT green.
    subject_mask = cv2.bitwise_not(green_mask)

    # Clean up speckle noise and smooth the edge so hair doesn't get chewed up.
    kernel = np.ones((5, 5), np.uint8)
    subject_mask = cv2.morphologyEx(subject_mask, cv2.MORPH_OPEN, kernel)
    subject_mask = cv2.morphologyEx(subject_mask, cv2.MORPH_CLOSE, kernel)
    subject_mask = cv2.GaussianBlur(subject_mask, (7, 7), 0)

    # Keep only the largest connected blob (the person), drop stray fragments.
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        (subject_mask > 127).astype(np.uint8), connectivity=8
    )
    if num_labels > 1:
        largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        clean = np.zeros_like(subject_mask)
        clean[labels == largest] = 255
        subject_mask = cv2.GaussianBlur(clean, (7, 7), 0)

    return subject_mask


def main():
    if len(sys.argv) != 2:
        print("usage: python scripts/prep_photo.py <source-photo.jpg>")
        sys.exit(1)

    src_path = sys.argv[1]
    bgr = cv2.imread(src_path)
    if bgr is None:
        print(f"could not read {src_path}")
        sys.exit(1)

    alpha = key_out_green(bgr)

    # Composite onto pure white using the alpha mask.
    alpha_f = (alpha.astype(np.float32) / 255.0)[..., None]
    white = np.full_like(bgr, 255, dtype=np.uint8)
    composited = (bgr.astype(np.float32) * alpha_f +
                  white.astype(np.float32) * (1 - alpha_f)).astype(np.uint8)

    # Grayscale + CLAHE for real highlight/shadow separation on the face.
    gray = cv2.cvtColor(composited, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    # Re-flatten the background to pure white (CLAHE can slightly gray it).
    bg_mask = alpha < 40
    contrasted[bg_mask] = 255

    out_path = "prepped.png"
    cv2.imwrite(out_path, contrasted)
    print(f"wrote {out_path}  ({contrasted.shape[1]}x{contrasted.shape[0]})")


if __name__ == "__main__":
    main()
