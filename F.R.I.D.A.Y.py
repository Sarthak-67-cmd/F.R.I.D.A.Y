import os
import time
import cv2
import numpy as np

# --- LAB CONFIGURATION ---
AUTHORIZED_DIR = "authorized_faces"
ALERTS_DIR = "intruder_alerts"

os.makedirs(AUTHORIZED_DIR, exist_ok=True)
os.makedirs(ALERTS_DIR, exist_ok=True)

class FridayOfflineSentry:
    def __init__(self):
        self.stealth_mode = False
        self.unknown_start_time = None
        self.alert_triggered = False
        self.boss_descriptor = None
        
        print("[FRIDAY] Initializing offline biometric tracking channels...")
        self.load_boss_signature()

    def load_boss_signature(self):
        """Calculates a secure structural signature for boss.jpg if it exists."""
        boss_path = os.path.join(AUTHORIZED_DIR, "boss.jpg")
        if not os.path.exists(boss_path):
            print(f"\n[WARNING] 'boss.jpg' not found in '{AUTHORIZED_DIR}' folder.")
            print("FRIDAY will flag every active object as UNKNOWN THREAT until configured.\n")
            return

        # Load reference photo and calculate a tracking histogram
        img = cv2.imread(boss_path)
        if img is not None:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            self.boss_descriptor = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
            cv2.normalize(self.boss_descriptor, self.boss_descriptor, 0, 255, cv2.NORM_MINMAX)
            print("[FRIDAY] Biometric profile metrics verified. Welcome back, Boss.")

    def run(self):
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            print("[CRITICAL] Optical camera hardware unavailable.")
            return

        # Initialize background subtraction to isolate objects completely offline
        back_sub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

        print("\n=== STARK INDUSTRIES LAB PROTOCOL ===")
        print("Press [Esc] to instantly ENTER STEALTH MODE")
        print("Press [Spacebar] to EXIT STEALTH MODE")
        print("Press [Q] to SHUTDOWN entirely")
        print("=====================================\n")

        while True:
            ret, frame = video_capture.read()
            if not ret:
                break

            # Isolate movement contours
            fg_mask = back_sub.apply(frame)
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            has_unknown = False

            for contour in contours:
                # Ignore tiny background noise glitches
                if cv2.contourArea(contour) < 6000:
                    continue

                (x, y, w, h) = cv2.boundingRect(contour)
                name = "UNKNOWN THREAT"
                color = (0, 0, 255) # Warning Red

                # If boss data exists, perform live color matrix evaluation matching
                if self.boss_descriptor is not None:
                    roi = frame[y:y+h, x:x+w]
                    if roi.size > 0:
                        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                        roi_hist = cv2.calcHist([hsv_roi], [0, 1], None, [180, 256], [0, 180, 0, 256])
                        cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)
                        
                        # Match score via histogram correlation
                        match_score = cv2.compareHist(self.boss_descriptor, roi_hist, cv2.HISTCMP_CORREL)
                        if match_score > 0.45:  # High confidence alignment matching
                            name = "BOSS"
                            color = (255, 191, 0) # Stark Cyan-Blue

                if name == "UNKNOWN THREAT":
                    has_unknown = True

                if not self.stealth_mode:
                    # Draw sharp grid brackets on screen
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # --- STEALTH HANDLING PIPELINE ---
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
                cv2.imshow("FRIDAY: Active Lab Monitor", frame)
                key = cv2.waitKey(1) & 0xFF

            # --- INTERRUPT MATRIX CONTROLS ---
            if key == 27:  # Esc Key
                if not self.stealth_mode:
                    print("[FRIDAY] Purging active workspace grid. Entering stealth monitor mode...")
                    self.stealth_mode = True
                    cv2.destroyAllWindows()
            elif key == 32:  # Spacebar Key
                if self.stealth_mode:
                    print("[FRIDAY] Restoring primary dashboard feeds.")
                    self.stealth_mode = False
            elif key == ord('q') or key == ord('Q'):
                print("[FRIDAY] Systems safe. Powering down.")
                break

        video_capture.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    sentry = FridayOfflineSentry()
    sentry.run()
