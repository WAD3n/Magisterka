# Instalacja wymaganych pakietów
install.packages("dplyr")
install.packages("neuralnet")
install.packages("nnet")
install.packages("randomForest")
install.packages("xgboost")

# Ładowanie bibliotek
library(dplyr)
library(neuralnet)
library(nnet)
library(randomForest)
library(xgboost)

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

# Pętla przechodząca po kazdym z unikalnych symboli z pliku z pliku z symbolami
for (index in uniqueIndexes) {

  # Wyswietlenie informacji ile iteracji pozostalo do skonczenia

  iteration <- iteration + 1
  cat('Przetwarzanie symbolu:', index, 'Iteracja:', iteration, "z: ", length(uniqueIndexes), '\n')

  # Wyfiltrowanie danych z wartościami spółek dla symbolu z aktualnej iteracji
  indexedData <- filter(data, symbol == index)

  # Usunięcie kolumn nieużytecznych dla predykcji
  indexedData <- indexedData %>% select(-datetime, -symbol)

  # TRENOWANIE MODELU RANDOM FOREST

  # Podział danych na zestawy treningowe i testowe
  trainingIndicates <- sample(1:nrow(indexedData), 0.7 * nrow(indexedData))
  trainingData <- indexedData[trainingIndicates, ]
  testingData <- indexedData[-trainingIndicates, ]

  # Określenie liczby drzew dla modelu
  k <- 15

  # Wytrenowanie modelu Random Forest
  modelRF <- randomForest(open ~ ., data = trainingData, ntree = k)

  # Ocena modelu Random Forest


  # TRENOWANIE MODELU XGBOOST

  # Przygotowanie danych dla XGBoost
  xAxisTraining <- as.matrix(trainingData %>% select(-open))
  yAxisTraining <- trainingData$open

  xAxisTesting <- as.matrix(testingData %>% select(-open))
  yAxisTesting <- testingData$open

  dTrain <- xgb.DMatrix(data = xAxisTraining, label = yAxisTraining)
  dTest <- xgb.DMatrix(data = xAxisTesting, label = yAxisTesting)

  # Parametry dla modelu XGBoost
  params <- list(
    objective = "reg:squarederror",
    eval_metric = "rmse",
    eta = 0.1,
    max_depth = 6
  )

  # Trenowanie modelu XGBoost
  modelXGB <- xgb.train(
    params = params,
    data = dTrain,
    nrounds = 100,
    watchlist = list(train = dTrain, test = dTest),
    verbose = 1
  )

  # Ocena modelu XGBoost
  predictionXGB <- predict(modelXGB, dTest)
  rmse <- sqrt(mean((predictionXGB - yAxisTesting)^2))
  print(paste("RMSE dla zestawu testowego:", round(rmse, 2)))

  # TRENOWANIE MODELU SVM

    # Wykorzystujemy poprzednio przygotowane dane dla modelu RandomForest

    modelSVM <- svm( open ~ ., data = trainingData , kernel = 'radial' , cost = 1 , gamma = 0.1)

    # Predykowanie na podstawie modelu SVM

    predictionSVM <- predict(modelSVM, newdata = testingData)

    # Ocena Modelu




}


# lstm
# nnet
# neurlanet