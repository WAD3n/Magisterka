library(ggplot2)
library(dplyr)
library(tidyr)

# Ścieżki do plików
results_file <- 'predictions.csv'
output_dir <- 'graphs/'

# Wczytywanie wyników
results <- read.csv(results_file)

# Tworzenie folderu, jeśli nie istnieje
if (!dir.exists(output_dir)) {
  dir.create(output_dir)
}

# Lista unikalnych symboli
unique_symbols <- unique(results$symbol)

# Funkcja do tworzenia wykresów dla danego symbolu
create_plots <- function(symbol) {
  symbol_data <- filter(results, symbol == symbol)
  
  print(paste("Processing symbol:", symbol))
  print(symbol_data)
  
  # Wykres RMSE
  rmse_data <- symbol_data %>%
    select(model, rmse_open, rmse_high, rmse_low, rmse_close) %>%
    pivot_longer(cols = starts_with("rmse"), names_to = "metric", values_to = "value")
  
  print("RMSE data:")
  print(rmse_data)
  
  rmse_plot <- ggplot(rmse_data, aes(x = model, y = value, fill = metric)) +
    geom_bar(stat = "identity", position = "dodge") +
    labs(title = paste("RMSE for", symbol), x = "Model", y = "RMSE") +
    theme_minimal()
  
  ggsave(filename = paste0(output_dir, "rmse_", gsub(":", "_", symbol), ".png"), plot = rmse_plot, width = 7, height = 7)
  
  # Wykres Accuracy
  accuracy_data <- symbol_data %>%
    select(model, accuracy_open, accuracy_high, accuracy_low, accuracy_close) %>%
    pivot_longer(cols = starts_with("accuracy"), names_to = "metric", values_to = "value")
  
  print("Accuracy data:")
  print(accuracy_data)
  
  accuracy_plot <- ggplot(accuracy_data, aes(x = model, y = value, fill = metric)) +
    geom_bar(stat = "identity", position = "dodge") +
    labs(title = paste("Accuracy for", symbol), x = "Model", y = "Accuracy") +
    theme_minimal()
  
  ggsave(filename = paste0(output_dir, "accuracy_", gsub(":", "_", symbol), ".png"), plot = accuracy_plot, width = 7, height = 7)
}

# Tworzenie wykresów dla wszystkich symboli
for (symbol in unique_symbols) {
  create_plots(symbol)
}

# Tworzenie zbiorczych wykresów dla wszystkich symboli

# Obliczanie średnich wartości dla każdego modelu
average_rmse <- results %>%
  group_by(model) %>%
  summarise(across(starts_with("rmse"), ~ mean(.x, na.rm = TRUE)))

average_accuracy <- results %>%
  group_by(model) %>%
  summarise(across(starts_with("accuracy"), ~ mean(.x, na.rm = TRUE)))

# Wykres zbiorczy RMSE
rmse_data_all <- average_rmse %>%
  pivot_longer(cols = starts_with("rmse"), names_to = "metric", values_to = "value")

rmse_plot_all <- ggplot(rmse_data_all, aes(x = model, y = value, color = metric, group = metric)) +
  geom_point(size = 3) +
  geom_line() +
  labs(title = "Average RMSE for all models", x = "Model", y = "RMSE") +
  theme_minimal()

ggsave(filename = paste0(output_dir, "rmse_all_models.png"), plot = rmse_plot_all, width = 7, height = 7)

# Wykres zbiorczy Accuracy
accuracy_data_all <- average_accuracy %>%
  pivot_longer(cols = starts_with("accuracy"), names_to = "metric", values_to = "value")

accuracy_plot_all <- ggplot(accuracy_data_all, aes(x = model, y = value, color = metric, group = metric)) +
  geom_point(size = 3) +
  geom_line() +
  labs(title = "Average Accuracy for all models", x = "Model", y = "Accuracy") +
  theme_minimal()

ggsave(filename = paste0(output_dir, "accuracy_all_models.png"), plot = accuracy_plot_all, width = 7, height = 7)
