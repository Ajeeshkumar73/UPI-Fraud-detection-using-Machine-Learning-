from django.core.management.base import BaseCommand
from ml.train_model import train_and_evaluate_models

class Command(BaseCommand):
    help = 'Trains ML fraud classification models (Logistic Regression, Random Forest, XGBoost) and selects the best model.'

    def handle(self, *args, **options):
        self.stdout.write("==========================================")
        self.stdout.write(" STARTING ML FRAUD MODEL TRAINING PIPELINE")
        self.stdout.write("==========================================")
        try:
            metadata = train_and_evaluate_models()
            self.stdout.write(self.style.SUCCESS(f"\n--> Model Training Completed! Selected Model: {metadata['selected_model']}"))
            self.stdout.write("\nModel Performance Comparison:")
            self.stdout.write(f"{'Model':<22} | {'Accuracy':<8} | {'Precision':<9} | {'Recall':<6} | {'F1':<6} | {'ROC-AUC':<7} | {'PR-AUC':<6}")
            self.stdout.write("-" * 80)
            for m_name, metrics in metadata['model_comparison'].items():
                self.stdout.write(f"{m_name:<22} | {metrics['accuracy']:<8} | {metrics['precision']:<9} | {metrics['recall']:<6} | {metrics['f1']:<6} | {metrics['roc_auc']:<7} | {metrics['pr_auc']:<6}")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error training models: {str(e)}"))
