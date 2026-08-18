import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import face_recognition
import numpy as np
import csv
from datetime import datetime
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from utils import (BG_COLOR, BG_SECONDARY, CARD_COLOR, TEXT_COLOR, TEXT_SECONDARY,
                   PRIMARY_COLOR, SECONDARY_COLOR, WARNING_COLOR, BORDER_COLOR,
                   SUCCESS_COLOR, DANGER_COLOR, FONT_HEADER, FONT_BODY, FONT_BODY_BOLD,
                   FONT_SMALL, FONT_TITLE,
                   create_button, show_error, show_info, center_window)


class EvaluateModelApp:
    """Evaluates the trained face recognition model using Leave-One-Out Cross-Validation."""

    def __init__(self, root, preloaded_data=None):
        """
        Args:
            root: Tkinter Toplevel or Tk window.
            preloaded_data: Optional dict with 'encodings' (list of np arrays)
                            and 'names' (list of strings) to skip re-encoding.
        """
        self.root = root
        self.root.title("Model Evaluation — Metrics")
        self.root.configure(bg=BG_COLOR)
        center_window(self.root, 780, 680)
        self.root.resizable(True, True)
        self.root.grab_set()

        self.preloaded_data = preloaded_data
        self.results = {}  # Stores computed metrics

        self._build_ui()
        # Auto-start evaluation
        self._start_evaluation_thread()

    # ──────────────────────────────────────────────────────────────
    #                           UI
    # ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Top accent bar
        tk.Frame(self.root, bg=SECONDARY_COLOR, height=3).pack(fill="x")

        # Header
        header = tk.Frame(self.root, bg=BG_SECONDARY, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="📊", font=("Segoe UI", 22), bg=BG_SECONDARY).pack(side="left", padx=(25, 10))

        header_text = tk.Frame(header, bg=BG_SECONDARY)
        header_text.pack(side="left", fill="y", pady=8)
        tk.Label(header_text, text="MODEL EVALUATION", font=FONT_HEADER, bg=BG_SECONDARY, fg=TEXT_COLOR).pack(anchor="w")
        tk.Label(header_text, text="Leave-One-Out Cross-Validation metrics", font=FONT_SMALL, bg=BG_SECONDARY, fg=TEXT_SECONDARY).pack(anchor="w")

        tk.Frame(self.root, bg=BORDER_COLOR, height=1).pack(fill="x")

        # ── Loading / progress area ──
        self.loading_frame = tk.Frame(self.root, bg=BG_COLOR, padx=40, pady=40)
        self.loading_frame.pack(fill="both", expand=True)

        self.lbl_status = tk.Label(self.loading_frame, text="Initializing evaluation…", font=FONT_BODY_BOLD, bg=BG_COLOR, fg=WARNING_COLOR)
        self.lbl_status.pack(pady=(20, 5))

        self.lbl_detail = tk.Label(self.loading_frame, text="Loading face encodings from dataset", font=FONT_SMALL, bg=BG_COLOR, fg=TEXT_SECONDARY)
        self.lbl_detail.pack(pady=(0, 20))

        style = ttk.Style()
        style.configure("Eval.Horizontal.TProgressbar", troughcolor=BG_SECONDARY, background=SECONDARY_COLOR, borderwidth=0, thickness=8)
        self.progress = ttk.Progressbar(self.loading_frame, orient="horizontal", length=400, mode="determinate", style="Eval.Horizontal.TProgressbar")
        self.progress.pack(pady=(0, 5))

        self.lbl_percent = tk.Label(self.loading_frame, text="0%", font=FONT_SMALL, bg=BG_COLOR, fg=SECONDARY_COLOR)
        self.lbl_percent.pack()

        # ── Results area (hidden initially) ──
        self.results_frame = tk.Frame(self.root, bg=BG_COLOR)

    # ──────────────────────────────────────────────────────────────
    #                   EVALUATION LOGIC
    # ──────────────────────────────────────────────────────────────

    def _start_evaluation_thread(self):
        threading.Thread(target=self._run_evaluation, daemon=True).start()

    def _update_progress(self, value, status_text=None, detail_text=None):
        """Thread-safe UI update helper."""
        self.root.after(0, lambda: self.progress.config(value=value))
        self.root.after(0, lambda: self.lbl_percent.config(text=f"{int(value)}%"))
        if status_text:
            self.root.after(0, lambda t=status_text: self.lbl_status.config(text=t))
        if detail_text:
            self.root.after(0, lambda t=detail_text: self.lbl_detail.config(text=t))

    def _run_evaluation(self):
        """Perform LOOCV evaluation."""
        try:
            # Step 1: Get encodings
            if self.preloaded_data:
                encodings = self.preloaded_data["encodings"]
                names = self.preloaded_data["names"]
                self._update_progress(10, "Using preloaded encodings…", f"Loaded {len(encodings)} face encodings")
            else:
                encodings, names = self._load_encodings_from_dataset()

            if not encodings or len(encodings) < 2:
                self.root.after(0, lambda: show_error("Error", "Need at least 2 face encodings to evaluate. Please capture more faces."))
                self.root.after(0, self.root.destroy)
                return

            unique_persons = sorted(set(names))
            total = len(encodings)

            self._update_progress(15, "Running Leave-One-Out CV…", f"{total} samples, {len(unique_persons)} person(s)")

            # Step 2: LOOCV
            y_true = []
            y_pred = []

            for i in range(total):
                # Leave one out
                test_encoding = encodings[i]
                test_label = names[i]

                train_encodings = encodings[:i] + encodings[i+1:]
                train_names = names[:i] + names[i+1:]

                # Predict using same logic as recognize.py
                matches = face_recognition.compare_faces(train_encodings, test_encoding, tolerance=0.5)
                face_distances = face_recognition.face_distance(train_encodings, test_encoding)

                predicted = "UNKNOWN"
                if len(face_distances) > 0:
                    best_idx = np.argmin(face_distances)
                    if matches[best_idx]:
                        predicted = train_names[best_idx]

                y_true.append(test_label)
                y_pred.append(predicted)

                # Update progress: map i from 0..total-1 to 15..85
                pct = 15 + int((i + 1) / total * 70)
                if i % max(1, total // 20) == 0:
                    self._update_progress(pct, detail_text=f"Evaluating sample {i+1}/{total}")

            self._update_progress(90, "Computing metrics…", "Calculating accuracy, precision, recall, F1")

            # Step 3: Compute metrics
            # Build label set: all unique persons + UNKNOWN if any prediction was UNKNOWN
            all_labels = sorted(set(y_true + y_pred))

            acc = accuracy_score(y_true, y_pred)
            precision, recall, f1, support = precision_recall_fscore_support(
                y_true, y_pred, labels=all_labels, zero_division=0
            )
            cm = confusion_matrix(y_true, y_pred, labels=all_labels)

            # Per-person metrics
            per_person = []
            for idx, label in enumerate(all_labels):
                per_person.append({
                    "name": label,
                    "precision": round(precision[idx] * 100, 2),
                    "recall": round(recall[idx] * 100, 2),
                    "f1": round(f1[idx] * 100, 2),
                    "support": int(support[idx]),
                })

            # Macro averages
            macro_precision = round(np.mean(precision) * 100, 2)
            macro_recall = round(np.mean(recall) * 100, 2)
            macro_f1 = round(np.mean(f1) * 100, 2)

            self.results = {
                "accuracy": round(acc * 100, 2),
                "total_samples": total,
                "total_persons": len(unique_persons),
                "per_person": per_person,
                "confusion_matrix": cm,
                "labels": all_labels,
                "macro_precision": macro_precision,
                "macro_recall": macro_recall,
                "macro_f1": macro_f1,
                "y_true": y_true,
                "y_pred": y_pred,
            }

            self._update_progress(100, "✓ Evaluation Complete!", f"Accuracy: {self.results['accuracy']}%")

            # Show results UI
            self.root.after(300, self._show_results)

        except Exception as e:
            self.root.after(0, lambda err=str(e): show_error("Evaluation Error", f"An error occurred:\n{err}"))
            self.root.after(0, self.root.destroy)

    def _load_encodings_from_dataset(self):
        """Load face encodings directly from the dataset folder."""
        dataset_path = "dataset"
        if not os.path.exists(dataset_path):
            self.root.after(0, lambda: show_error("Error", "Dataset folder not found!"))
            self.root.after(0, self.root.destroy)
            return [], []

        persons = [d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))]
        if not persons:
            self.root.after(0, lambda: show_error("Error", "No user data found in dataset!"))
            self.root.after(0, self.root.destroy)
            return [], []

        encodings = []
        names = []
        total_persons = len(persons)

        for pi, person_name in enumerate(persons):
            self._update_progress(
                int((pi / total_persons) * 10),
                f"Encoding: {person_name}",
                f"Loading person {pi+1}/{total_persons}"
            )
            person_folder = os.path.join(dataset_path, person_name)
            images = os.listdir(person_folder)

            for img_name in images:
                if not img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                img_path = os.path.join(person_folder, img_name)
                try:
                    image = face_recognition.load_image_file(img_path)
                    encs = face_recognition.face_encodings(image)
                    if len(encs) > 0:
                        encodings.append(encs[0])
                        names.append(person_name)
                except Exception:
                    pass

        return encodings, names

    # ──────────────────────────────────────────────────────────────
    #                   RESULTS DISPLAY
    # ──────────────────────────────────────────────────────────────

    def _show_results(self):
        """Replace loading UI with results display."""
        self.loading_frame.pack_forget()

        self.results_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Create a canvas with scrollbar for the entire results area
        canvas = tk.Canvas(self.results_frame, bg=BG_COLOR, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg=BG_COLOR)

        scroll_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(scroll_content, bg=BG_COLOR, padx=30, pady=20)
        content.pack(fill="both", expand=True)

        # ── Summary Cards Row ──
        summary_row = tk.Frame(content, bg=BG_COLOR)
        summary_row.pack(fill="x", pady=(0, 15))

        self._create_metric_card(summary_row, "🎯 Accuracy", f"{self.results['accuracy']}%",
                                  SUCCESS_COLOR if self.results['accuracy'] >= 80 else WARNING_COLOR if self.results['accuracy'] >= 50 else DANGER_COLOR)
        self._create_metric_card(summary_row, "📊 Precision", f"{self.results['macro_precision']}%", SECONDARY_COLOR)
        self._create_metric_card(summary_row, "🔁 Recall", f"{self.results['macro_recall']}%", PRIMARY_COLOR)
        self._create_metric_card(summary_row, "⚖ F1-Score", f"{self.results['macro_f1']}%", WARNING_COLOR)

        # ── Dataset Info ──
        info_frame = tk.Frame(content, bg=CARD_COLOR, padx=15, pady=10)
        info_frame.pack(fill="x", pady=(0, 15))
        tk.Label(info_frame,
                 text=f"📁 {self.results['total_samples']} total samples  ·  👤 {self.results['total_persons']} person(s)  ·  Tolerance: 0.5",
                 font=FONT_SMALL, bg=CARD_COLOR, fg=TEXT_SECONDARY).pack()

        # ── Per-Person Metrics Table ──
        self._create_section_header(content, "📋 Per-Person Classification Report")
        self._create_metrics_table(content)

        # ── Confusion Matrix ──
        self._create_section_header(content, "🔢 Confusion Matrix")
        self._create_confusion_matrix(content)

        # ── Export Button ──
        tk.Frame(content, bg=BG_COLOR, height=15).pack()
        btn_row = tk.Frame(content, bg=BG_COLOR)
        btn_row.pack(fill="x")

        export_btn = create_button(btn_row, "💾  Export Report (CSV)", self._export_csv, bg_color=SECONDARY_COLOR, width=22, height=2)
        export_btn.pack(side="left", padx=(0, 10))

        close_btn = create_button(btn_row, "✕  Close", self.root.destroy, bg_color="#666666", width=10, height=2)
        close_btn.pack(side="right")

        tk.Frame(content, bg=BG_COLOR, height=20).pack()

        # Update canvas scroll region after widgets are placed
        self.root.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _create_metric_card(self, parent, title, value, color):
        """Small summary metric card."""
        outer = tk.Frame(parent, bg=BORDER_COLOR)
        outer.pack(side="left", fill="both", expand=True, padx=5)

        card = tk.Frame(outer, bg=CARD_COLOR, padx=12, pady=12)
        card.pack(padx=1, pady=1, fill="both", expand=True)

        # Accent stripe
        tk.Frame(card, bg=color, height=2).pack(fill="x", pady=(0, 8))

        tk.Label(card, text=title, font=FONT_SMALL, bg=CARD_COLOR, fg=TEXT_SECONDARY).pack()
        tk.Label(card, text=value, font=("Segoe UI", 20, "bold"), bg=CARD_COLOR, fg=color).pack(pady=(2, 0))

    def _create_section_header(self, parent, text):
        """Section header with subtle separator."""
        frame = tk.Frame(parent, bg=BG_COLOR)
        frame.pack(fill="x", pady=(10, 8))
        tk.Label(frame, text=text, font=FONT_BODY_BOLD, bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor="w")
        tk.Frame(frame, bg=BORDER_COLOR, height=1).pack(fill="x", pady=(4, 0))

    def _create_metrics_table(self, parent):
        """Per-person precision/recall/F1/support table."""
        table_frame = tk.Frame(parent, bg=BORDER_COLOR)
        table_frame.pack(fill="x", pady=(0, 10))

        inner = tk.Frame(table_frame, bg=CARD_COLOR)
        inner.pack(padx=1, pady=1, fill="x")

        columns = ["Person", "Precision", "Recall", "F1-Score", "Support"]

        # Header row
        header_row = tk.Frame(inner, bg=BG_SECONDARY)
        header_row.pack(fill="x")
        for col_idx, col_name in enumerate(columns):
            lbl = tk.Label(header_row, text=col_name, font=("Segoe UI", 9, "bold"),
                           bg=BG_SECONDARY, fg=PRIMARY_COLOR, padx=10, pady=6, anchor="w")
            lbl.pack(side="left", fill="x", expand=True)

        # Data rows
        for i, person in enumerate(self.results["per_person"]):
            row_bg = CARD_COLOR if i % 2 == 0 else BG_SECONDARY
            row = tk.Frame(inner, bg=row_bg)
            row.pack(fill="x")

            values = [
                person["name"],
                f"{person['precision']}%",
                f"{person['recall']}%",
                f"{person['f1']}%",
                str(person["support"]),
            ]

            for val in values:
                lbl = tk.Label(row, text=val, font=FONT_SMALL, bg=row_bg, fg=TEXT_COLOR, padx=10, pady=5, anchor="w")
                lbl.pack(side="left", fill="x", expand=True)

        # Macro average row
        macro_row = tk.Frame(inner, bg=CARD_COLOR)
        macro_row.pack(fill="x")
        tk.Frame(macro_row, bg=PRIMARY_COLOR, height=1).pack(fill="x")

        avg_frame = tk.Frame(macro_row, bg=CARD_COLOR)
        avg_frame.pack(fill="x")

        macro_vals = [
            "MACRO AVG",
            f"{self.results['macro_precision']}%",
            f"{self.results['macro_recall']}%",
            f"{self.results['macro_f1']}%",
            str(self.results['total_samples']),
        ]

        for val in macro_vals:
            lbl = tk.Label(avg_frame, text=val, font=("Segoe UI", 9, "bold"),
                           bg=CARD_COLOR, fg=WARNING_COLOR, padx=10, pady=6, anchor="w")
            lbl.pack(side="left", fill="x", expand=True)

    def _create_confusion_matrix(self, parent):
        """NxN confusion matrix displayed as a table with color coding."""
        labels = self.results["labels"]
        cm = self.results["confusion_matrix"]

        cm_frame = tk.Frame(parent, bg=BORDER_COLOR)
        cm_frame.pack(fill="x", pady=(0, 10))

        inner = tk.Frame(cm_frame, bg=CARD_COLOR, padx=10, pady=10)
        inner.pack(padx=1, pady=1, fill="x")

        # Label: Predicted →
        tk.Label(inner, text="Predicted →", font=("Segoe UI", 8, "bold"),
                 bg=CARD_COLOR, fg=TEXT_SECONDARY).pack(anchor="e", padx=5)

        # Header row with label names
        n = len(labels)
        header_row = tk.Frame(inner, bg=CARD_COLOR)
        header_row.pack(fill="x")

        # Corner cell
        tk.Label(header_row, text="Actual ↓", font=("Segoe UI", 8, "bold"),
                 bg=CARD_COLOR, fg=TEXT_SECONDARY, width=14, anchor="w", padx=5).pack(side="left")

        for label in labels:
            display = label[:12] + "…" if len(label) > 12 else label
            tk.Label(header_row, text=display, font=("Segoe UI", 8, "bold"),
                     bg=CARD_COLOR, fg=PRIMARY_COLOR, width=10, padx=3, pady=3).pack(side="left")

        # Data rows
        max_val = cm.max() if cm.size > 0 else 1
        for row_idx in range(n):
            row = tk.Frame(inner, bg=CARD_COLOR)
            row.pack(fill="x")

            # Row label
            display = labels[row_idx][:12] + "…" if len(labels[row_idx]) > 12 else labels[row_idx]
            tk.Label(row, text=display, font=("Segoe UI", 8, "bold"),
                     bg=CARD_COLOR, fg=TEXT_COLOR, width=14, anchor="w", padx=5).pack(side="left")

            for col_idx in range(n):
                val = cm[row_idx][col_idx]
                # Color: green for diagonal (correct), red tint for off-diagonal
                if row_idx == col_idx:
                    cell_fg = SUCCESS_COLOR
                    cell_bg = "#1a2e1a" if val > 0 else CARD_COLOR
                else:
                    cell_fg = DANGER_COLOR if val > 0 else TEXT_SECONDARY
                    cell_bg = "#2e1a1a" if val > 0 else CARD_COLOR

                tk.Label(row, text=str(val), font=("Segoe UI", 9, "bold"),
                         bg=cell_bg, fg=cell_fg, width=10, padx=3, pady=3,
                         relief="groove", bd=1).pack(side="left")

    # ──────────────────────────────────────────────────────────────
    #                       EXPORT
    # ──────────────────────────────────────────────────────────────

    def _export_csv(self):
        """Export the evaluation report as a CSV file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            title="Export Evaluation Report"
        )

        if not filepath:
            return

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Summary section
                writer.writerow(["=== Model Evaluation Report ==="])
                writer.writerow(["Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(["Overall Accuracy", f"{self.results['accuracy']}%"])
                writer.writerow(["Total Samples", self.results['total_samples']])
                writer.writerow(["Total Persons", self.results['total_persons']])
                writer.writerow(["Macro Precision", f"{self.results['macro_precision']}%"])
                writer.writerow(["Macro Recall", f"{self.results['macro_recall']}%"])
                writer.writerow(["Macro F1-Score", f"{self.results['macro_f1']}%"])
                writer.writerow([])

                # Per-person metrics
                writer.writerow(["=== Per-Person Metrics ==="])
                writer.writerow(["Person", "Precision (%)", "Recall (%)", "F1-Score (%)", "Support"])
                for person in self.results["per_person"]:
                    writer.writerow([person["name"], person["precision"], person["recall"], person["f1"], person["support"]])
                writer.writerow([])

                # Confusion matrix
                writer.writerow(["=== Confusion Matrix ==="])
                labels = self.results["labels"]
                cm = self.results["confusion_matrix"]
                writer.writerow(["Actual \\ Predicted"] + labels)
                for i, label in enumerate(labels):
                    writer.writerow([label] + [str(v) for v in cm[i]])

            show_info("Export Successful", f"Report saved to:\n{filepath}")
        except Exception as e:
            show_error("Export Error", f"Failed to save report:\n{e}")
