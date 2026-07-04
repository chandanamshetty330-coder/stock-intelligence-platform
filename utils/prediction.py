import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os
import warnings
warnings.filterwarnings('ignore')

def prepare_lstm_data(df, lookback=60):
    """Prepare data for LSTM"""
    data = df['Close'].values.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)

    X, y = [], []
    for i in range(lookback, len(scaled_data)):
        X.append(scaled_data[i-lookback:i, 0])
        y.append(scaled_data[i, 0])

    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    return X, y, scaler

def train_lstm_model(df, lookback=60, epochs=20, progress_callback=None):
    """Train real LSTM model with progress bar"""
    try:
        import torch
        import torch.nn as nn

        class LSTMModel(nn.Module):
            def __init__(self, input_size=1, hidden_size=64, num_layers=2, dropout=0.2):
                super(LSTMModel, self).__init__()
                self.hidden_size = hidden_size
                self.num_layers = num_layers
                self.lstm = nn.LSTM(
                    input_size, hidden_size,
                    num_layers, batch_first=True,
                    dropout=dropout
                )
                self.fc1 = nn.Linear(hidden_size, 32)
                self.fc2 = nn.Linear(32, 1)
                self.relu = nn.ReLU()

            def forward(self, x):
                h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
                c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
                out, _ = self.lstm(x, (h0, c0))
                out = self.relu(self.fc1(out[:, -1, :]))
                out = self.fc2(out)
                return out

        # Prepare data
        X, y, scaler = prepare_lstm_data(df, lookback)

        # Split 80/20
        split = int(len(X) * 0.8)
        X_train = torch.FloatTensor(X[:split])
        y_train = torch.FloatTensor(y[:split])
        X_test = torch.FloatTensor(X[split:])
        y_test = torch.FloatTensor(y[split:])

        # Initialize model
        model = LSTMModel()
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        scheduler = torch.optim.lr_scheduler.StepLR(
            optimizer, step_size=10, gamma=0.5)

        # Training loop
        train_losses = []
        model.train()

        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = model(X_train)
            loss = criterion(outputs.squeeze(), y_train)
            loss.backward()
            optimizer.step()
            scheduler.step()
            train_losses.append(loss.item())

            if progress_callback:
                progress_callback(epoch + 1, epochs, loss.item())

        # Evaluate
        model.eval()
        with torch.no_grad():
            test_pred = model(X_test).squeeze().numpy()
            y_test_np = y_test.numpy()

        # Inverse transform
        test_pred_actual = scaler.inverse_transform(
            test_pred.reshape(-1, 1)).flatten()
        y_test_actual = scaler.inverse_transform(
            y_test_np.reshape(-1, 1)).flatten()

        # Metrics
        mae = mean_absolute_error(y_test_actual, test_pred_actual)
        rmse = np.sqrt(mean_squared_error(y_test_actual, test_pred_actual))
        mape = np.mean(np.abs(
            (y_test_actual - test_pred_actual) / y_test_actual)) * 100
        accuracy = 100 - mape

        return {
            'model': model,
            'scaler': scaler,
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'accuracy': accuracy,
            'train_losses': train_losses,
            'test_pred': test_pred_actual,
            'test_actual': y_test_actual
        }

    except Exception as e:
        print(f"LSTM Error: {e}")
        return None

def predict_future_lstm(model_data, df, days=7, lookback=60):
    """Predict future prices using trained LSTM"""
    try:
        import torch

        model = model_data['model']
        scaler = model_data['scaler']

        data = df['Close'].values.reshape(-1, 1)
        scaled_data = scaler.transform(data)

        last_sequence = scaled_data[-lookback:]
        predictions = []
        current_seq = last_sequence.copy()

        model.eval()
        with torch.no_grad():
            for _ in range(days):
                x = torch.FloatTensor(
                    current_seq.reshape(1, lookback, 1))
                pred = model(x).item()
                predictions.append(pred)
                current_seq = np.append(
                    current_seq[1:], [[pred]], axis=0)

        predictions = np.array(predictions).reshape(-1, 1)
        predictions = scaler.inverse_transform(predictions).flatten()

        last_date = df['Date'].iloc[-1]
        future_dates = pd.date_range(
            start=last_date, periods=days + 1, freq='B')[1:]

        pred_df = pd.DataFrame({
            'Date': future_dates,
            'Predicted_Price': predictions,
            'Upper_Bound': predictions * 1.02,
            'Lower_Bound': predictions * 0.98
        })

        return pred_df

    except Exception as e:
        print(f"Prediction error: {e}")
        return None

def predict_future(df, days=7, lookback=60):
    """Simple trend-based prediction as fallback"""
    try:
        data = df['Close'].values.reshape(-1, 1)
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(data)

        last_sequence = scaled_data[-lookback:]
        predictions = []
        current_seq = last_sequence.copy()

        for _ in range(days):
            trend = np.mean(np.diff(current_seq[-10:], axis=0))
            next_val = current_seq[-1] + trend
            next_val = np.clip(next_val, 0, 1)
            predictions.append(next_val[0])
            current_seq = np.append(
                current_seq[1:], [[next_val[0]]], axis=0)

        predictions = np.array(predictions).reshape(-1, 1)
        predictions = scaler.inverse_transform(predictions)

        last_date = df['Date'].iloc[-1]
        future_dates = pd.date_range(
            start=last_date, periods=days + 1, freq='B')[1:]

        pred_df = pd.DataFrame({
            'Date': future_dates,
            'Predicted_Price': predictions.flatten(),
            'Upper_Bound': predictions.flatten() * 1.02,
            'Lower_Bound': predictions.flatten() * 0.98
        })

        return pred_df

    except Exception as e:
        print(f"Prediction Error: {e}")
        return None

def calculate_metrics(df):
    """Calculate technical indicators"""
    df = df.copy()

    # Moving averages
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    df['BB_middle'] = df['Close'].rolling(window=20).mean()
    df['BB_upper'] = df['BB_middle'] + 2 * df['Close'].rolling(
        window=20).std()
    df['BB_lower'] = df['BB_middle'] - 2 * df['Close'].rolling(
        window=20).std()

    # Daily returns
    df['Daily_Return'] = df['Close'].pct_change() * 100

    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    return df