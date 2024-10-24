use magisterka;

-- Tworzenie tabeli prediction
CREATE TABLE prediction (
    UID            UNIQUEIDENTIFIER NOT NULL,  -- Unikalny identyfikator w formacie UUID
    model          VARCHAR(20) NOT NULL,       -- Model predykcji
    symbol         VARCHAR(20) NOT NULL,       -- Symbol gie�dowy
    predicted_open FLOAT NOT NULL,             -- Prognozowana cena otwarcia
    predicted_high FLOAT NOT NULL,             -- Prognozowana cena maksymalna
    predicted_low  FLOAT NOT NULL,             -- Prognozowana cena minimalna
    predicted_close FLOAT NOT NULL,            -- Prognozowana cena zamkni�cia
    rmse_open      FLOAT NOT NULL,             -- RMSE dla otwarcia
    rmse_high      FLOAT NOT NULL,             -- RMSE dla maksymalnej ceny
    rmse_low       FLOAT NOT NULL,             -- RMSE dla minimalnej ceny
    rmse_close     FLOAT NOT NULL,             -- RMSE dla zamkni�cia
    accuracy_open  FLOAT NOT NULL,             -- Dok�adno�� dla otwarcia
    accuracy_high  FLOAT NOT NULL,             -- Dok�adno�� dla maksymalnej ceny
    accuracy_low   FLOAT NOT NULL,             -- Dok�adno�� dla minimalnej ceny
    accuracy_close FLOAT NOT NULL,             -- Dok�adno�� dla zamkni�cia
    CONSTRAINT prediction_pk PRIMARY KEY (UID) -- Klucz g��wny
);

-- Tworzenie tabeli "User"
CREATE TABLE [User] (
    username VARCHAR(20) NOT NULL,   -- Nazwa u�ytkownika
    password VARBINARY(MAX) NOT NULL, -- Has�o u�ytkownika (zakodowane)
    CONSTRAINT user_pk PRIMARY KEY (username) -- Klucz g��wny
);

-- Tworzenie tabeli wallet
CREATE TABLE wallet (
    UID             UNIQUEIDENTIFIER NOT NULL,   -- Unikalny identyfikator portfela
    name            VARCHAR(30) NOT NULL,        -- Nazwa portfela
    user_username   VARCHAR(20) NOT NULL,        -- Nazwa u�ytkownika powi�zana z portfelem
    CONSTRAINT wallet_pk PRIMARY KEY (UID, user_username), -- Klucz g��wny
    CONSTRAINT wallet_user_fk FOREIGN KEY (user_username) REFERENCES [User](username) -- Klucz obcy
);

-- Tworzenie tabeli wallet_prediction
CREATE TABLE wallet_prediction (
    wallet_uid           UNIQUEIDENTIFIER NOT NULL, -- UID portfela
    wallet_user_username VARCHAR(20) NOT NULL,      -- U�ytkownik portfela
    prediction_uid       UNIQUEIDENTIFIER NOT NULL, -- UID predykcji
    CONSTRAINT relation_2_pk PRIMARY KEY (wallet_uid, wallet_user_username, prediction_uid), -- Klucz g��wny
    CONSTRAINT relation_2_prediction_fk FOREIGN KEY (prediction_uid) REFERENCES prediction(UID), -- Klucz obcy do prediction
    CONSTRAINT relation_2_wallet_fk1 FOREIGN KEY (wallet_uid, wallet_user_username) REFERENCES wallet(UID, user_username) -- Klucz obcy do wallet
);

-- W��czenie sprawdzania integralno�ci danych oraz relacji
ALTER TABLE wallet_prediction
    ADD CONSTRAINT relation_2_wallet_fk1 FOREIGN KEY (wallet_uid, wallet_user_username)
        REFERENCES wallet (UID, user_username);

ALTER TABLE wallet_prediction
    ADD CONSTRAINT relation_2_prediction_fk FOREIGN KEY (prediction_uid)
        REFERENCES prediction (UID);
