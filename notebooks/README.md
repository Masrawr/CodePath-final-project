# Notebooks

`finetune.ipynb` (to be added) fine-tunes a small DistilBERT/CodeBERT classifier
on `data/bugs.csv` to predict a bug category, then saves the model to `model/`.

Intended to run on a free Google Colab GPU. Steps:
1. Upload `data/bugs.csv`.
2. Load `distilbert-base-uncased` with a classification head (6 labels).
3. Fine-tune, plot the loss curve, and print a confusion matrix on the test split.
4. Download the saved model into the local `model/` folder.
