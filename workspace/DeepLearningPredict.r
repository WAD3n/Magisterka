# Instalacja wymaganych pakietów
install.packages("dplyr")
install.packages("neuralnet")
install.packages("nnet")
install.packages("randomForest")
install.packages("xgboost")
install.packages("e1071")

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
  rmseRF <- sqrt(mean((predictionRF - testingData$open)^2))
  cat("Zakończono trenowanie Random Forest dla symbolu:", index, "\n")
  cat("RMSE dla modelu Random Forest:", round(rmseRF, 2), "\n")
  
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
  cat("Zakończono trenowanie XGBoost dla symbolu:", index, "\n")
  cat("RMSE dla modelu XGBoost:", round(rmseXGB, 2), "\n")
  
  # TRENOWANIE MODELU SVM
  modelSVM <- svm(open ~ ., data = trainingData, kernel = 'radial', cost = 1, gamma = 0.1)
  predictionSVM <- predict(modelSVM, newdata = testingData)
  rmseSVM <- sqrt(mean((predictionSVM - testingData$open)^2))
  cat("Zakończono trenowanie SVM dla symbolu:", index, "\n")
  cat("RMSE dla modelu SVM:", round(rmseSVM, 2), "\n")
  
  # TRENOWANIE MODELU NNET
  nnetNeurons <- 100
  modelNNET <- nnet(open ~ ., data = trainingData, size = nnetNeurons, maxit = 200)
  predictionNNET <- predict(modelNNET, newdata = testingData)
  rmseNNET <- sqrt(mean((predictionNNET - testingData$open)^2))
  cat("Zakończono trenowanie NNET dla symbolu:", index, "\n")
  cat("RMSE dla modelu NNET:", round(rmseNNET, 2), "\n")
  
  # TRENOWANIE MODELU NEURALNET
  modelNEURALNET <- neuralnet(
    open ~ .,
    data = trainingData,
    hidden = c(5, 1),
    linear.output = TRUE,
    stepmax = 1e6
  )
  plot(modelNEURALNET) # Wizualizacja
  
  # Predykcja za pomocą neuralnet
  predictionNEURALNET <- compute(modelNEURALNET, testingData %>% select(-open))$net.result
  rmseNEURALNET <- sqrt(mean((predictionNEURALNET - testingData$open)^2))
  cat("Zakończono trenowanie NEURALNET dla symbolu:", index, "\n")
  cat("RMSE dla modelu NEURALNET:", round(rmseNEURALNET, 2), "\n")
}
