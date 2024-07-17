library(dplyr)
library(neuralnet)
library(nnet)
library(uuid)

# Ścieżki do plików
fileToAnalize <- 'workspace/companyValues.csv'
fileWithIndexes <- 'workspace/companies_symbol.csv'

# Wczytywanie danych
data <- read.csv(fileToAnalize)
indexes <- read.csv(fileWithIndexes)

# Dodanie przedrostka "NASDAQ:" do symboli
indexes$symbol <- paste0("NASDAQ:", indexes$symbol)

# Uzyskiwanie unikalnych symboli
uniqueIndexes <- unique(indexes$symbol)

# Przygotowanie pliku do zapisu wyników
results <- data.frame(uid = character(), model = character(), symbol = character(), predicted_open = numeric(),
                      predicted_high = numeric(), predicted_low = numeric(), predicted_close = numeric(),
                      rmse_open = numeric(), rmse_high = numeric(), rmse_low = numeric(), rmse_close = numeric(),
                      accuracy_open = numeric(), accuracy_high = numeric(), accuracy_low = numeric(), accuracy_close = numeric(), stringsAsFactors = FALSE)

# Funkcja do obliczania RMSE
rmse <- function(actual, predicted) {
  sqrt(mean((actual - predicted)^2))
}

# Funkcja do obliczania accuracy
accuracy <- function(actual, predicted, threshold = 0.03) {
  mean(abs(actual - predicted) / actual < threshold)
}

# Pętla po indeksach
for (index in uniqueIndexes) {
  # Filtrowanie danych dla danego indeksu
  indexedData <- filter(data, symbol == index)
  
  if (nrow(indexedData) >= 30) {
    input_data <- indexedData[, c("open", "high", "low", "volume")]
    output_data <- indexedData[, c("open", "high", "low", "close")]
    
    # Trening Neuralnet
    nn <- neuralnet(open + high + low + close ~ open + high + low + volume, data = data.frame(input_data, output_data), hidden = 5, linear.output = TRUE)
    nn_pred <- compute(nn, as.data.frame(tail(input_data, 1)))$net.result
    
    if (!is.null(nn_pred) && length(nn_pred) == 4) {
      nn_next_pred <- nn_pred[1, ]
      
      # Obliczanie RMSE i accuracy dla Neuralnet na podstawie ostatnich 5 danych
      nn_last5_actual <- tail(output_data, 5)
      nn_last5_pred <- compute(nn, as.data.frame(tail(input_data, 5)))$net.result
      rmse_nn_open <- rmse(nn_last5_actual$open, nn_last5_pred[, 1])
      rmse_nn_high <- rmse(nn_last5_actual$high, nn_last5_pred[, 2])
      rmse_nn_low <- rmse(nn_last5_actual$low, nn_last5_pred[, 3])
      rmse_nn_close <- rmse(nn_last5_actual$close, nn_last5_pred[, 4])
      accuracy_nn_open <- accuracy(nn_last5_actual$open, nn_last5_pred[, 1])
      accuracy_nn_high <- accuracy(nn_last5_actual$high, nn_last5_pred[, 2])
      accuracy_nn_low <- accuracy(nn_last5_actual$low, nn_last5_pred[, 3])
      accuracy_nn_close <- accuracy(nn_last5_actual$close, nn_last5_pred[, 4])
      
      results <- rbind(results, data.frame(uid = UUIDgenerate(),model = "Neuralnet", symbol = index,
                                           predicted_open = nn_next_pred[1], predicted_high = nn_next_pred[2],
                                           predicted_low = nn_next_pred[3], predicted_close = nn_next_pred[4],
                                           rmse_open = rmse_nn_open, rmse_high = rmse_nn_high, rmse_low = rmse_nn_low, rmse_close = rmse_nn_close,
                                           accuracy_open = accuracy_nn_open, accuracy_high = accuracy_nn_high, accuracy_low = accuracy_nn_low, accuracy_close = accuracy_nn_close))
    }
    
    # Trening Nnet
    nnet_model <- nnet(cbind(open, high, low, close) ~ open + high + low + volume, data = data.frame(input_data, output_data), size = 5, linout = TRUE)
    nnet_pred <- predict(nnet_model, newdata = as.data.frame(tail(input_data, 1)))
    
    if (!is.null(nnet_pred) && ncol(nnet_pred) == 4) {
      nnet_next_pred <- nnet_pred[1, ]
      
      # Obliczanie RMSE i accuracy dla Nnet na podstawie ostatnich 5 danych
      nnet_last5_actual <- tail(output_data, 5)
      nnet_last5_pred <- predict(nnet_model, newdata = as.data.frame(tail(input_data, 5)))
      rmse_nnet_open <- rmse(nnet_last5_actual$open, nnet_last5_pred[, 1])
      rmse_nnet_high <- rmse(nnet_last5_actual$high, nnet_last5_pred[, 2])
      rmse_nnet_low <- rmse(nnet_last5_actual$low, nnet_last5_pred[, 3])
      rmse_nnet_close <- rmse(nnet_last5_actual$close, nnet_last5_pred[, 4])
      accuracy_nnet_open <- accuracy(nnet_last5_actual$open, nnet_last5_pred[, 1])
      accuracy_nnet_high <- accuracy(nnet_last5_actual$high, nnet_last5_pred[, 2])
      accuracy_nnet_low <- accuracy(nnet_last5_actual$low, nnet_last5_pred[, 3])
      accuracy_nnet_close <- accuracy(nnet_last5_actual$close, nnet_last5_pred[, 4])
      
      results <- rbind(results, data.frame(uid = UUIDgenerate(),model = "Nnet", symbol = index,
                                           predicted_open = nnet_next_pred[1], predicted_high = nnet_next_pred[2],
                                           predicted_low = nnet_next_pred[3], predicted_close = nnet_next_pred[4],
                                           rmse_open = rmse_nnet_open, rmse_high = rmse_nnet_high, rmse_low = rmse_nnet_low, rmse_close = rmse_nnet_close,
                                           accuracy_open = accuracy_nnet_open, accuracy_high = accuracy_nnet_high, accuracy_low = accuracy_nnet_low, accuracy_close = accuracy_nnet_close))
    }
  }
}

# Zapisywanie wyników do pliku CSV
write.csv(results, "workspace/predictions.csv", row.names = FALSE)
