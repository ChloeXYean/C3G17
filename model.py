import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import joblib

# Load the dataset
# Replace 'air_quality_data.csv' with the path to your dataset
data = pd.read_csv('air_quality_data.csv')

# Preprocessing steps (assuming the data is clean)
# Selecting features and target
features = ['feature1', 'feature2', 'feature3'] # Replace with your actual feature column names
target = 'pm25' # Replace with your actual target column name

X = data[features]
y = data[target]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create and train the Linear Regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Save the trained model to a file
joblib.dump(model, 'linear_regression_model.joblib')

print("Model trained and saved as linear_regression_model.joblib")
