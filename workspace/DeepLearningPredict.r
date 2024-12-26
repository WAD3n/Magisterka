# Instalacja wymaganych pakietów
# install.packages("dplyr")
# install.packages("neuralnet")
# install.packages("nnet")
# install.packages("randomForest")
# install.packages("xgboost")
# install.packages("e1071")

# Ładowanie bibliotek
library(dplyr)
library(neuralnet)
library(nnet)
library(randomForest)
library(xgboost)
library(e1071)

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

# Licznik iteracji
iteration <- 0

# PRZZYGOTWANIE RAMKI DANYCH DO ZAPISU WYNIKOW

set.seed(123)

results <- data.frame(
  symbol = character(),
  model = character(),
  rmse = numeric(),
  mse = numeric(),
  smape = numeric(),
  mape = numeric(),
  rSquered = numeric(),
  huberLoss = numeric(),
  actualValue = numeric(),
  futureValue = numeric(),
  effectivenss = numeric(),
  stringsAsFactors = FALSE
)

# OKREŚLENIE WAG DLA METRYK

weights <- list(
  rmse = 0.1,
  mse = 0.1,
  smape = 0.2,
  mape = 0.2,
  r_squared = 0.2,
  huber_loss = 0.2
)

# RMSE (Root Mean Squared Error)
rmse <- function(actual, predicted) {
  sqrt(mean((actual - predicted)^2))
}

# MSE (Mean Squared Error)
mse <- function(actual, predicted) {
  mean((actual - predicted)^2)
}

# SMAPE (Symmetric Mean Absolute Percentage Error)
smape <- function(actual, predicted) {
  mean(2 * abs(actual - predicted) / (abs(actual) + abs(predicted))) * 100
}

# MAPE (Mean Absolute Percentage Error)
mape <- function(actual, predicted) {
  mean(abs((actual - predicted) / actual)) * 100
}

# R^2 (Coefficient of Determination)
r_squared <- function(actual, predicted) {
  ss_total <- sum((actual - mean(actual))^2)
  ss_residual <- sum((actual - predicted)^2)
  1 - (ss_residual / ss_total)
}

# Huber Loss
huber_loss <- function(actual, predicted, delta = 1) {
  residual <- actual - predicted
  huber <- ifelse(
    abs(residual) <= delta,
    0.5 * residual^2,
    delta * abs(residual) - 0.5 * delta^2
  )
  mean(huber)
}

calculate_effectiveness <- function(rmse, mse, smape, mape, r_squared, huber_loss, weights, actual_values) {
  # Zakres danych rzeczywistych
  range_values <- max(actual_values) - min(actual_values)
  mean_value <- mean(actual_values)
  
  # Zabezpieczenie przed dzieleniem przez 0
  range_values <- ifelse(range_values == 0, 1, range_values)
  mean_value <- ifelse(mean_value == 0, 1, mean_value)
  
  # Normalizacja RMSE i MSE przez zakres lub średnią wartości rzeczywistych
  normalized_rmse <- rmse / range_values
  normalized_mse <- mse / range_values
  
  # Normalizacja pozostałych metryk w ich standardowych zakresach
  effectiveness <- sum(
    weights$rmse * (1 - normalized_rmse),
    weights$mse * (1 - normalized_mse),
    weights$smape * (1 - smape / 100),       # SMAPE w procentach (0-100)
    weights$mape * (1 - mape / 100),         # MAPE w procentach (0-100)
    weights$r_squared * r_squared,           # R^2 już jest w zakresie [0,1]
    weights$huber_loss * (1 - huber_loss / range_values) # Huber Loss normalizowany przez zakres
  )
  
  # Zabezpieczenie przed negatywnymi wartościami
  effectiveness <- max(effectiveness, 0)
  
  return(round(effectiveness * 100, 2)) # Wynik w procentach
}

weighted_averages <- function(results, x, y) {
  # Sprawdzenie, czy ramka danych nie jest pusta
  if (nrow(results) == 0) {
    stop("The 'results' data frame is empty. Please provide valid data.")
  }
  
  # Lista metryk do uwzględnienia
  metrics <- c("rmse", "mse", "huberLoss", "smape", "mape", "rSquered", "actualValue", "futureValue")
  
  # Sprawdzenie, czy wszystkie wymagane metryki są obecne w danych
  missing_metrics <- setdiff(metrics, colnames(results))
  if (length(missing_metrics) > 0) {
    stop(paste("The following metrics are missing from the 'results' data frame:", paste(missing_metrics, collapse = ", ")))
  }
  
  # Wyliczanie ważonych średnich dla każdej metryki
  weighted_means <- sapply(metrics, function(metric) {
    # Wartości kolumny
    values <- results[[metric]]
    # Wagi (efektywność)
    weights <- results$effectiveness
    # Obliczanie ważonej średniej z obsługą braków danych (NA)
    if (all(is.na(values)) || sum(weights, na.rm = TRUE) == 0) {
      return(NA)  # Zwrot NA, jeśli brak danych lub suma wag jest zerowa
    }
    sum(values * weights, na.rm = TRUE) / sum(weights, na.rm = TRUE)
  })
  
  # Obliczenie ważonej efektywności (średnia ważona efektywności)
  weighted_effectiveness <- sum(results$effectiveness * results$effectiveness, na.rm = TRUE) / sum(results$effectiveness, na.rm = TRUE)
  weighted_effectiveness <- round(weighted_effectiveness,digits=2)
  cat("Procentowa wazona skutecznosc modeli:", weighted_effectiveness, "%\n")
  
  # Dodanie kolumny symbolu (indeksu)
  index_name <- unique(results$symbol)
  if (length(index_name) > 1) {
    warning("Multiple symbols found in 'results'. Using the first symbol.")
    index_name <- index_name[1]
  }
  
  # Dodanie indeksu do wyników
  weighted_means <- c(index = index_name, weighted_means, effectiveness = weighted_effectiveness)
  
  # Konwersja wyniku na ramkę danych
  weighted_means <- as.data.frame(t(weighted_means), stringsAsFactors = FALSE)
  
  # Czyszczenie ramki `results`
  results <<- data.frame()
  
  # Sprawdzenie, czy efektywność mieści się w przedziale (x, y)
if ((weighted_effectiveness >= x && weighted_effectiveness <= y)) {
    # Dopisanie do pliku CSV, jeśli warunek jest spełniony
    write.table(weighted_means, 
                file = "model_results.csv", 
                sep = ",", 
                row.names = FALSE, 
                col.names = !file.exists("model_results.csv"), # Dodaj nagłówki tylko raz
                append = TRUE)  # Dopisuj wyniki do pliku
    message("Results appended to CSV.")
} else {
    message("Effectiveness out of range. Results not saved.")
}
  
  return(weighted_means)
}



# Pętla przechodząca po każdym z unikalnych symboli z pliku z symbolami
for (index in uniqueIndexes) {
  
  # Wyswietlenie informacji ile iteracji pozostalo do skonczenia
  iteration <- iteration + 1
  cat('Przetwarzanie symbolu:', index, 'Iteracja:', iteration, "z:", length(uniqueIndexes), '\n')
  
  # Wyfiltrowanie danych z wartościami spółek dla symbolu z aktualnej iteracji
  indexedData <- filter(data, symbol == index)
  
  # Usunięcie kolumn nieużytecznych dla predykcji
  indexedData <- indexedData %>% select(-datetime, -symbol)
  
  # Podział danych na zestawy treningowe i testowe
  trainingIndicates <- sample(1:nrow(indexedData), 0.7 * nrow(indexedData))
  trainingData <- indexedData[trainingIndicates, ]
  testingData <- indexedData[-trainingIndicates, ]
  
  # TRENOWANIE MODELU RANDOM FOREST
  k <- 15 # Liczba drzew
  modelRF <- randomForest(open ~ ., data = trainingData, ntree = k)
  predictionRF <- predict(modelRF, newdata = testingData)
  rmseRF <- round(rmse(testingData$open, predictionRF),2)
  mseRF <- round(mse(testingData$open, predictionRF), 2)
  smapeRF <- round(smape(testingData$open, predictionRF), 2)
  mapeRF <- round(mape(testingData$open, predictionRF), 2)
  rSqueredRF <- round(r_squared(testingData$open, predictionRF), 2)
  huberLossRF <- round(huber_loss(testingData$open, predictionRF), 2)
  

  # TRENOWANIE MODELU XGBOOST
  xAxisTraining <- as.matrix(trainingData %>% select(-open))
  yAxisTraining <- trainingData$open
  xAxisTesting <- as.matrix(testingData %>% select(-open))
  yAxisTesting <- testingData$open
  
  dTrain <- xgb.DMatrix(data = xAxisTraining, label = yAxisTraining)
  dTest <- xgb.DMatrix(data = xAxisTesting, label = yAxisTesting)
  
  params <- list(
    objective = "reg:squarederror",
    eval_metric = "rmse",
    eta = 0.1,
    max_depth = 6
  )
  
  modelXGB <- xgb.train(
    params = params,
    data = dTrain,
    nrounds = 100,
    watchlist = list(train = dTrain, test = dTest),
    verbose = 1
  )
  predictionXGB <- predict(modelXGB, dTest)
  rmseXGB <- sqrt(mean((predictionXGB - yAxisTesting)^2))
  rmseXGB <- round(rmse(testingData$open, predictionXGB), 2)
  mseXGB <- round(mse(testingData$open, predictionXGB), 2)
  smapeXGB <- round(smape(testingData$open, predictionXGB), 2)
  mapeXGB <- round(mape(testingData$open, predictionXGB), 2)
  rSqueredXGB <- round(r_squared(testingData$open, predictionXGB), 2)
  huberLossXGB <- round(huber_loss(testingData$open, predictionXGB), 2)
  
  # TRENOWANIE MODELU SVM
  modelSVM <- svm(open ~ ., data = trainingData, kernel = 'radial', cost = 1, gamma = 0.1)
  predictionSVM <- predict(modelSVM, newdata = testingData)
  rmseSVM <- sqrt(mean((predictionSVM - testingData$open)^2))
  rmseSVM <- round(rmse(testingData$open, predictionSVM), 2)
  mseSVM <- round(mse(testingData$open, predictionSVM), 2)
  smapeSVM <- round(smape(testingData$open, predictionSVM), 2)
  mapeSVM <- round(mape(testingData$open, predictionSVM), 2)
  rSqueredSVM <- round(r_squared(testingData$open, predictionSVM), 2)
  huberLossSVM <- round(huber_loss(testingData$open, predictionSVM), 2)

  # TRENOWANIE MODELU NNET
  nnetNeurons <- 10
  modelNNET <- nnet(open ~ ., data = trainingData, size = nnetNeurons, maxit = 200, decay = 0.01, linout = TRUE)
  predictionNNET <- predict(modelNNET, newdata = testingData)
  rmseNNET <- round(rmse(testingData$open, predictionNNET), 2)
  mseNNET <- round(mse(testingData$open, predictionNNET), 2)
  smapeNNET <- round(smape(testingData$open, predictionNNET), 2)
  mapeNNET <- round(mape(testingData$open, predictionNNET), 2)
  rSqueredNNET <- round(r_squared(testingData$open, predictionNNET), 2)
  huberLossNNET <- round(huber_loss(testingData$open, predictionNNET), 2)
  
  # TRENOWANIE MODELU NEURALNET
  modelNEURALNET <- neuralnet(
    open ~ .,
    data = trainingData,
    hidden = c(5, 3),
    linear.output = TRUE,
    stepmax = 1e6
  )

  
  # Predykcja za pomocą neuralnet
  predictionNEURALNET <- compute(modelNEURALNET, testingData %>% select(-open))$net.result
  rmseNEURALNET <- round(rmse(testingData$open, predictionNEURALNET), 2)
  mseNEURALNET <- round(mse(testingData$open, predictionNEURALNET), 2)
  smapeNEURALNET <- round(smape(testingData$open, predictionNEURALNET), 2)
  mapeNEURALNET <- round(mape(testingData$open, predictionNEURALNET), 2)
  rSqueredNEURALNET <- round(r_squared(testingData$open, predictionNEURALNET), 2)
  huberLossNEURALNET <- round(huber_loss(testingData$open, predictionNEURALNET), 2)


  # OCENA MODELI

effectivenessRF <- calculate_effectiveness(rmseRF, mseRF, smapeRF, mapeRF, rSqueredRF, huberLossRF, weights, testingData$open)
effectivenessXGB <- calculate_effectiveness(rmseXGB, mseXGB, smapeXGB, mapeXGB, rSqueredXGB, huberLossXGB, weights, testingData$open)
effectivenessSVM <- calculate_effectiveness(rmseSVM, mseSVM, smapeSVM, mapeSVM, rSqueredSVM, huberLossSVM, weights, testingData$open)
effectivenessNNET <- calculate_effectiveness(rmseNNET, mseNNET, smapeNNET, mapeNNET, rSqueredNNET, huberLossNNET, weights, testingData$open)
effectivenessNEURALNET <- calculate_effectiveness(rmseNEURALNET, mseNEURALNET, smapeNEURALNET, mapeNEURALNET, rSqueredNEURALNET, huberLossNEURALNET, weights, testingData$open)

  
  cat("Procentowa skuteczność modelu Random Forest:", effectivenessRF, "%\n")
  cat("Procentowa skuteczność modelu XGB:", effectivenessXGB, "%\n")
  cat("Procentowa skuteczność modelu SVM:", effectivenessSVM, "%\n")
  cat("Procentowa skuteczność modelu NNET:", effectivenessNNET, "%\n")
  cat("Procentowa skuteczność modelu NEURALNET:", effectivenessNEURALNET, "%\n")

  # PREDYKOWANNIE WARTOŚCI 
  
 results <- rbind(results, 
                   data.frame(symbol = index, model = "Random Forest", rmse = rmseRF,
                              mse = mseRF,
                              huberLoss = huberLossRF,
                              smape = smapeRF,
                              mape = mapeRF,
                              rSquered = rSqueredRF,
                              actualValue = tail(testingData$open, 1), 
                              futureValue = round(tail(predictionRF, 1),2),
                              effectiveness = effectivenessRF))
  results <- rbind(results, 
                   data.frame(symbol = index, model = "XGBoost", rmse = rmseXGB,
                              mse = mseXGB,
                              huberLoss = huberLossXGB,
                              smape = smapeXGB,
                              mape = mapeXGB,
                              rSquered = rSqueredXGB,
                              actualValue = tail(testingData$open, 1), 
                              futureValue = round(tail(predictionXGB, 1), 2),
                              effectiveness = effectivenessXGB))
results <- rbind(results, 
                   data.frame(symbol = index, model = "SVM", rmse = rmseSVM,
                              mse = mseSVM,
                              huberLoss = huberLossSVM,
                              smape = smapeSVM,
                              mape = mapeSVM,
                              rSquered = rSqueredSVM,
                              actualValue = tail(testingData$open, 1), 
                              futureValue = round(tail(predictionSVM, 1), 2),
                              effectiveness = effectivenessSVM))
                
  results <- rbind(results, 
                 data.frame(symbol = index, model = "NNET", rmse = rmseNNET,
                            mse = mseNNET,
                            huberLoss = huberLossNNET,
                            smape = smapeNNET,
                            mape = mapeNNET,
                            rSquered = rSqueredNNET,
                            actualValue = tail(testingData$open, 1), 
                            futureValue = round(tail(predictionNNET, 1), 2),
                            effectiveness = effectivenessNNET))


  results <- rbind(results, 
                 data.frame(symbol = index, model = "NeuralNet", rmse = rmseNEURALNET,
                            mse = mseNEURALNET,
                            huberLoss = huberLossNEURALNET,
                            smape = smapeNEURALNET,
                            mape = mapeNEURALNET,
                            rSquered = rSqueredNEURALNET,
                            actualValue = tail(testingData$open, 1), 
                            futureValue = round(tail(predictionNEURALNET, 1), 2),
                            effectiveness = effectivenessNEURALNET))

weighted_results <- weighted_averages(results, 60, 90)
}