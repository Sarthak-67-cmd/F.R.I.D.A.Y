import os
import time
import cv2
import numpy as np

# --- LAB CONFIGURATION ---
AUTHORIZED_DIR = "authorized_faces"
ALERTS_DIR = "intruder_alerts"

os.makedirs(AUTHORIZED_DIR, exist_ok=True)
os.makedirs(ALERTS_DIR, exist_ok=True)

class FridayOfflineHUD:
    def __init__(self):
        self.stealth_mode = False
        self.unknown_start_time = None
        self.alert_triggered = False
        self.boss_descriptor = None
        
        print("[FRIDAY] Initializing holographic tracking matrix channels...")
        self.load_boss_signature()

    def load_boss_signature(self):
        """Calculates structural metrics for boss.jpg if it exists."""
        boss_path = os.path.join(AUTHORIZED_DIR, "boss.jpg")
        if not os.path.exists(boss_path):
            print(f"\n[WARNING] 'boss.jpg' not found in '{AUTHORIZED_DIR}' folder.")
            print("FRIDAY will flag all targets as UNKNOWN THREAT until configured.\n")
            return

        img = cv2.imread(boss_path)
        if img is not None:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            self.boss_descriptor = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
            cv2.normalize(self.boss_descriptor, self.boss_descriptor, 0, 255, cv2.NORM_MINMAX)
            print("[FRIDAY] Biometric metrics loaded. Systems operational, Boss.")

    def draw_hud_brackets(self, img, x, y, w, h, color):
        """Draws sharp, high-tech corner brackets around targets instead of regular boxes."""
        length = 20
        thickness = 2
        
        # Top-Left corner
        cv2.line(img, (x, y), (x + length, y), color, thickness)
        cv2.line(img, (x, y), (x, y + length), color, thickness)
        
        # Top-Right corner
        cv2.line(img, (x + w, y), (x + w - length, y), color, thickness)
        cv2.line(img, (x + w, y), (x + w, y + length), color, thickness)
        
        # Bottom-Left corner
        cv2.line(img, (x, y + h), (x + length, y + h), color, thickness)
        cv2.line(img, (x, y + h), (x, y + h - length), color, thickness)
        
        # Bottom-Right corner
        cv2.line(img, (x + w, y + h), (x + w - length, y + h), color, thickness)
        cv2.line(img, (x + w, y + h), (x + w, y + h - length), color, thickness)

    def draw_global_overlay(self, img):
        """Draws a permanent Stark Industries targeting crosshair over the whole screen."""
        h, w, _ = img.shape
        cx, cy = w // 2, h // 2
        hud_color = (255, 191, 0) # Glowing Stark Cyan-Blue
        
        # Center target ring
        cv2.circle(img, (cx, cy), 40, hud_color, 1)
        cv2.circle(img, (cx, cy), 3, (0, 0, 255), -1) # Center red laser point
        
        # Crosshair lines
        cv2.line(img, (cx - 100, cy), (cx - 50, cy), hud_color, 1)
        cv2.line(img, (cx + 50, cy), (cx + 100, cy), hud_color, 1)
        cv2.line(img, (cx, cy - 100), (cx, cy - 50), hud_color, 1)
        cv2.line(img, (cx, cy + 50), (cx, cy + 100), hud_color, 1)
        
        # Telemetry Text Corner
        cv2.putText(img, "SYS: ACTIVE", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        cv2.putText(img, "SECURE MODE: LOG LOCAL", (15, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, hud_color, 1)

    def run(self):
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            print("[CRITICAL] Optical camera hardware unavailable.")
            return

        back_sub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

        while True:
            ret, frame = video_capture.read()
            if not ret:
                break

            fg_mask = back_sub.apply(frame)
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            has_unknown = False

            # Draw global interface overlay first
            if not self.stealth_mode:
                self.draw_global_overlay(frame)

            for contour in contours:
                if cv2.contourArea(contour) < 6000:
                    continue

                (x, y, w, h) = cv2.boundingRect(contour)
                name = "UNKNOWN THREAT"
                color = (0, 0, 255) # Threat Red

                if self.boss_descriptor is not None:
                    roi = frame[y:y+h, x:x+w]
                    if roi.size > 0:
                        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                        roi_hist = cv2.calcHist([hsv_roi], [0, 1], None, [180, 256], [0, 180, 0, 256])
                        cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)
                        
                        match_score = cv2.compareHist(self.boss_descriptor, roi_hist, cv2.HISTCMP_CORREL)
                        if match_score > 0.45:
                            name = "BOSS"
                            color = (255, 191, 0) # Stark Cyan-Blue

                if name == "UNKNOWN THREAT":
                    has_unknown = True

                if not self.stealth_mode:
                    # Draw high-tech tracking brackets and diagnostic data
                    self.draw_hud_brackets(frame, x, y, w, h, color)
                    cv2.putText(frame, f"TRK // {name}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            # --- STEALTH PIPELINE ---
            if self.stealth_mode:
                if has_unknown:
                    if self.unknown_start_time is None:
                        self.unknown_start_time = time.time()
                    elif time.time() - self.unknown_start_time >= 5.0 and not self.alert_triggered:
                        self.alert_triggered = True
                        snapshot_path = os.path.join(ALERTS_DIR, f"stealth_breach_{int(time.time())}.jpg")
                        cv2.imwrite(snapshot_path, frame)
                        print(f"⚠️ [STEALTH INTERCEPT] System logged movement telemetry to disk.")
                else:
                    self.unknown_start_time = None
                    self.alert_triggered = False
                    
                key = cv2.waitKey(200) & 0xFF
            else:
                cv2.imshow("FRIDAY: Tactical Sentry Monitor", frame)
                key = cv2.waitKey(1) & 0xFF

            # --- KEYBOARD CONTROLS ---
            if key == 27:  # Esc Key
                if not self.stealth_mode:
                    print("[FRIDAY] Terminal screen purged. Operating silently in background...")
                    self.stealth_mode = True
                    cv2.destroyAllWindows()
            elif key == 32:  # Spacebar Key
                if self.stealth_mode:
                    print("[FRIDAY] Activating display dashboard panels.")
                    self.stealth_mode = False
            elif key == ord('q') or key == ord('Q'):
                print("[FRIDAY] System powered down.")
                break

        video_capture.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    sentry = FridayOfflineHUD()
    sentry.run()
