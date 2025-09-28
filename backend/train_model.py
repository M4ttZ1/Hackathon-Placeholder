import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import joblib # Used for saving our model

print("Starting model training process for PHISHING detection...")

# 1. Load the dataset
DATASET_FILENAME = 'Phishing_Email.csv'
try:
    # This dataset has no header row, so we name the columns manually
    df = pd.read_csv(DATASET_FILENAME)
    # Ensure the column names match the CSV file, which are 'Email Text' and 'Email Type'
    df = df[['Email Text', 'Email Type']]
    df.columns = ['text', 'label'] # Rename for consistency
    print(f"Dataset loaded. Found {len(df)} emails.")
except FileNotFoundError:
    print(f"\nERROR: '{DATASET_FILENAME}' not found!")
    print("Please download the dataset from https://www.kaggle.com/datasets/subhajournal/phishing-email-dataset")
    print(f"And save it as '{DATASET_FILENAME}' in your 'backend' folder.\n")
    exit()
except KeyError:
    print(f"\nERROR: The CSV file '{DATASET_FILENAME}' does not contain the expected columns 'Email Text' and 'Email Type'.")
    print("Please ensure you are using the correct dataset.\n")
    exit()


# 2. Prepare the data
# Map the text labels to numerical values (0 for safe, 1 for phishing)
df['label'] = df['label'].map({'Safe Email': 0, 'Phishing Email': 1})
X = df['text']
y = df['label']

# Handle potential missing values in the text column
X = X.fillna('')

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print("Data split into training and testing sets.")

# 3. Create a TF-IDF Vectorizer
# This turns email text into a matrix of numerical features
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)
print("Text data has been vectorized.")

# 4. Train a Logistic Regression model
model = LogisticRegression(max_iter=1000)
model.fit(X_train_tfidf, y_train)
print("Model training complete.")

# 5. Evaluate the model (optional, but good practice)
accuracy = model.score(X_test_tfidf, y_test)
print(f"Model accuracy on test data: {accuracy:.4f}")

# 6. Save the trained vectorizer and model
# These files will be loaded by our FastAPI app
joblib.dump(vectorizer, 'vectorizer.joblib')
joblib.dump(model, 'model.joblib')

print("\nSuccess! The vectorizer and model have been saved as:")
print("- vectorizer.joblib")
print("- model.joblib")
print("\nYour FastAPI server will now use a model trained specifically on phishing emails.")