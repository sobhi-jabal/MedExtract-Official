"""
Metrics calculation utilities for extraction evaluation
Based on evaluation patterns from provided examples
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn import metrics as sklearn_metrics
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64


class MetricsCalculator:
    """
    Comprehensive metrics calculator for extraction evaluation
    Based on patterns from all provided examples
    """
    
    def __init__(self):
        self.supported_metrics = [
            "accuracy", "precision", "recall", "f1_score",
            "macro_precision", "micro_precision",
            "macro_recall", "micro_recall", 
            "macro_f1", "micro_f1"
        ]
    
    def calculate_accuracy(self, y_true: pd.Series, y_pred: pd.Series) -> Dict[str, float]:
        """
        Calculate accuracy metrics between ground truth and predictions
        Based on evaluate_experiment from original examples
        """
        # Clean and align data
        df_eval = pd.DataFrame({
            'true': y_true,
            'pred': y_pred
        }).dropna()
        
        if len(df_eval) == 0:
            return self._empty_metrics()
        
        y_true_clean = df_eval['true']
        y_pred_clean = df_eval['pred']
        
        # Calculate comprehensive metrics
        metrics_dict = {
            "accuracy": sklearn_metrics.accuracy_score(y_true_clean, y_pred_clean),
            "macro_precision": sklearn_metrics.precision_score(
                y_true_clean, y_pred_clean, average='macro', zero_division=0
            ),
            "micro_precision": sklearn_metrics.precision_score(
                y_true_clean, y_pred_clean, average='micro', zero_division=0
            ),
            "macro_recall": sklearn_metrics.recall_score(
                y_true_clean, y_pred_clean, average='macro', zero_division=0
            ),
            "micro_recall": sklearn_metrics.recall_score(
                y_true_clean, y_pred_clean, average='micro', zero_division=0
            ),
            "macro_f1": sklearn_metrics.f1_score(
                y_true_clean, y_pred_clean, average='macro', zero_division=0
            ),
            "micro_f1": sklearn_metrics.f1_score(
                y_true_clean, y_pred_clean, average='micro', zero_division=0
            ),
            "reports_evaluated": len(df_eval)
        }
        
        return metrics_dict
    
    def calculate_confusion_matrix(
        self, 
        y_true: pd.Series, 
        y_pred: pd.Series,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate confusion matrix with visualization
        Based on save_confusion_matrix from examples
        """
        # Clean data
        df_eval = pd.DataFrame({
            'true': y_true,
            'pred': y_pred
        }).dropna()
        
        if len(df_eval) == 0:
            return {"matrix": [], "labels": [], "visualization": None}
        
        y_true_clean = df_eval['true']
        y_pred_clean = df_eval['pred']
        
        # Determine labels
        if labels is None:
            all_labels = sorted(list(set(y_true_clean) | set(y_pred_clean)))
        else:
            all_labels = labels
        
        # Calculate confusion matrix
        cm = sklearn_metrics.confusion_matrix(
            y_true_clean, y_pred_clean, labels=all_labels
        )
        
        # Create visualization
        visualization = self._create_confusion_matrix_plot(cm, all_labels)
        
        return {
            "matrix": cm.tolist(),
            "labels": all_labels,
            "visualization": visualization,
            "total_samples": len(df_eval)
        }
    
    def calculate_btrads_distance(self, y_true: pd.Series, y_pred: pd.Series) -> Dict[str, float]:
        """
        Calculate BT-RADS specific distance metrics
        Based on calculate_btrads_distance from ds_btrads example
        """
        score_map = {
            "0": {"category": "baseline", "severity": 0},
            "1a": {"category": "improved", "severity": 1}, 
            "1b": {"category": "improved_med", "severity": 2},
            "2": {"category": "stable", "severity": 3},
            "3a": {"category": "worse_treatment", "severity": 4},
            "3b": {"category": "worse_indeterminate", "severity": 5},
            "3c": {"category": "worse_tumor", "severity": 6},
            "4": {"category": "highly_suspicious", "severity": 7}
        }
        
        distances = []
        valid_comparisons = 0
        
        for true_val, pred_val in zip(y_true, y_pred):
            if pd.isna(true_val) or pd.isna(pred_val):
                continue
                
            true_str = str(true_val).strip()
            pred_str = str(pred_val).strip()
            
            if true_str in score_map and pred_str in score_map:
                true_severity = score_map[true_str]["severity"]
                pred_severity = score_map[pred_str]["severity"]
                distance = abs(pred_severity - true_severity)
                distances.append(distance)
                valid_comparisons += 1
        
        if not distances:
            return {"mean_distance": -1, "valid_comparisons": 0}
        
        return {
            "mean_distance": np.mean(distances),
            "median_distance": np.median(distances),
            "max_distance": max(distances),
            "min_distance": min(distances),
            "valid_comparisons": valid_comparisons,
            "distance_distribution": np.bincount(distances).tolist()
        }
    
    def calculate_general_category_accuracy(
        self, 
        y_true: pd.Series, 
        y_pred: pd.Series,
        category_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """
        Calculate accuracy for general categories
        Based on get_general_category from ds_btrads example
        """
        if category_mapping is None:
            # Default BT-RADS mapping
            category_mapping = {
                "0": "0",
                "1a": "1", "1b": "1",
                "2": "2", 
                "3a": "3", "3b": "3", "3c": "3",
                "4": "4"
            }
        
        # Map to general categories
        y_true_general = y_true.map(category_mapping)
        y_pred_general = y_pred.map(category_mapping)
        
        # Calculate accuracy for general categories
        return self.calculate_accuracy(y_true_general, y_pred_general)
    
    def calculate_extraction_quality_metrics(
        self, 
        extracted_values: pd.Series,
        valid_values: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate quality metrics for extractions
        """
        total_extractions = len(extracted_values)
        
        if total_extractions == 0:
            return self._empty_quality_metrics()
        
        # Count different types of results
        invalid_count = (extracted_values == "invalid").sum()
        empty_count = extracted_values.isin(["", "NR", "unknown"]).sum()
        valid_count = total_extractions - invalid_count - empty_count
        
        # Calculate quality percentages
        quality_metrics = {
            "total_extractions": total_extractions,
            "valid_extractions": int(valid_count),
            "invalid_extractions": int(invalid_count),
            "empty_extractions": int(empty_count),
            "valid_percentage": (valid_count / total_extractions) * 100,
            "invalid_percentage": (invalid_count / total_extractions) * 100,
            "empty_percentage": (empty_count / total_extractions) * 100
        }
        
        # If valid values list provided, check compliance
        if valid_values is not None:
            compliant_count = extracted_values.isin(valid_values).sum()
            quality_metrics["compliant_extractions"] = int(compliant_count)
            quality_metrics["compliance_percentage"] = (compliant_count / total_extractions) * 100
        
        return quality_metrics
    
    def calculate_confidence_metrics(self, confidence_scores: pd.Series) -> Dict[str, float]:
        """Calculate metrics for confidence scores"""
        if len(confidence_scores) == 0:
            return {"mean_confidence": 0.0, "confidence_distribution": []}
        
        # Remove NaN values
        clean_scores = confidence_scores.dropna()
        
        if len(clean_scores) == 0:
            return {"mean_confidence": 0.0, "confidence_distribution": []}
        
        return {
            "mean_confidence": float(clean_scores.mean()),
            "median_confidence": float(clean_scores.median()),
            "std_confidence": float(clean_scores.std()),
            "min_confidence": float(clean_scores.min()),
            "max_confidence": float(clean_scores.max()),
            "confidence_distribution": self._create_confidence_distribution(clean_scores)
        }
    
    def _create_confusion_matrix_plot(
        self, 
        cm: np.ndarray, 
        labels: List[str]
    ) -> Optional[str]:
        """Create confusion matrix plot and return as base64 string"""
        try:
            plt.figure(figsize=(10, 8))
            sns.heatmap(
                cm, 
                annot=True, 
                fmt="d", 
                cmap='YlGnBu',
                xticklabels=labels, 
                yticklabels=labels
            )
            plt.xlabel('Predicted Labels')
            plt.ylabel('True Labels')
            plt.title('Confusion Matrix')
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            plt.tight_layout()
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            img_str = base64.b64encode(img_buffer.read()).decode()
            plt.close()
            
            return img_str
            
        except Exception as e:
            print(f"Error creating confusion matrix plot: {e}")
            plt.close()  # Ensure we close the figure
            return None
    
    def _create_confidence_distribution(self, scores: pd.Series) -> List[Dict[str, Any]]:
        """Create confidence score distribution data"""
        try:
            # Create bins for confidence scores
            bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
            bin_counts, bin_edges = np.histogram(scores, bins=bins)
            
            distribution = []
            for i, count in enumerate(bin_counts):
                distribution.append({
                    "range": f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}",
                    "count": int(count),
                    "percentage": (count / len(scores)) * 100
                })
            
            return distribution
            
        except Exception as e:
            print(f"Error creating confidence distribution: {e}")
            return []
    
    def _empty_metrics(self) -> Dict[str, float]:
        """Return empty metrics dictionary"""
        return {
            "accuracy": 0.0,
            "macro_precision": 0.0,
            "micro_precision": 0.0,
            "macro_recall": 0.0,
            "micro_recall": 0.0,
            "macro_f1": 0.0,
            "micro_f1": 0.0,
            "reports_evaluated": 0
        }
    
    def _empty_quality_metrics(self) -> Dict[str, Any]:
        """Return empty quality metrics dictionary"""
        return {
            "total_extractions": 0,
            "valid_extractions": 0,
            "invalid_extractions": 0,
            "empty_extractions": 0,
            "valid_percentage": 0.0,
            "invalid_percentage": 0.0,
            "empty_percentage": 0.0
        }
    
    def generate_comprehensive_report(
        self,
        results_df: pd.DataFrame,
        datapoint_configs: List[Dict[str, Any]],
        ground_truth_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive evaluation report"""
        report = {
            "summary": {},
            "datapoint_metrics": {},
            "overall_quality": {},
            "visualizations": {}
        }
        
        # Overall summary
        report["summary"] = {
            "total_rows": len(results_df),
            "datapoints_extracted": len(datapoint_configs),
            "has_ground_truth": ground_truth_column is not None and ground_truth_column in results_df.columns
        }
        
        # Per-datapoint analysis
        for dp_config in datapoint_configs:
            dp_name = dp_config.get("name", "unknown")
            cleaned_col = f"{dp_name}_cleaned"
            confidence_col = f"{dp_name}_confidence"
            
            if cleaned_col not in results_df.columns:
                continue
            
            # Quality metrics
            quality_metrics = self.calculate_extraction_quality_metrics(
                results_df[cleaned_col],
                dp_config.get("valid_values")
            )
            
            # Confidence metrics
            confidence_metrics = {}
            if confidence_col in results_df.columns:
                confidence_metrics = self.calculate_confidence_metrics(
                    results_df[confidence_col]
                )
            
            # Accuracy metrics (if ground truth available)
            accuracy_metrics = {}
            if ground_truth_column and ground_truth_column in results_df.columns:
                accuracy_metrics = self.calculate_accuracy(
                    results_df[ground_truth_column],
                    results_df[cleaned_col]
                )
            
            report["datapoint_metrics"][dp_name] = {
                "quality": quality_metrics,
                "confidence": confidence_metrics,
                "accuracy": accuracy_metrics
            }
        
        return report