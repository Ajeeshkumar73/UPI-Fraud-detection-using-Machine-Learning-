import os
import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Validates and displays summary of the Kaggle synthetic fraud dataset'

    def handle(self, *args, **options):
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'dataset', 'synthetic_fraud_dataset.csv')
        self.stdout.write(f"--> Checking dataset at: {csv_path}")

        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f"Dataset file not found at {csv_path}"))
            return

        df = pd.read_csv(csv_path)
        self.stdout.write(self.style.SUCCESS(f"Dataset Loaded Successfully!"))
        self.stdout.write(f"Records     : {len(df)}")
        self.stdout.write(f"Columns     : {len(df.columns)}")

        if 'Fraud_Label' in df.columns:
            fraud_cnt = int((df['Fraud_Label'] == 1).sum())
            gen_cnt = int((df['Fraud_Label'] == 0).sum())
            fraud_pct = round((fraud_cnt / len(df)) * 100, 2)
            self.stdout.write(f"Fraud Count : {fraud_cnt} ({fraud_pct}%)")
            self.stdout.write(f"Genuine Count: {gen_cnt}")
        else:
            self.stderr.write("Column 'Fraud_Label' missing!")

        missing = df.isnull().sum().sum()
        self.stdout.write(f"Total Missing Values: {missing}")
