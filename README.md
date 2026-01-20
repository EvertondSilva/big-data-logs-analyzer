# 🚀 NASA Access Logs - ETL Pipeline & Analytics Dashboard

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![PySpark](https://img.shields.io/badge/PySpark-3.5.0-orange.svg)](https://spark.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://www.postgresql.org/)
[![Dash](https://img.shields.io/badge/Dash-2.14.2-00D4FF.svg)](https://plotly.com/dash/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Pipeline completo de ETL e análise de logs de acesso da NASA (Julho 1995) usando PySpark, PostgreSQL e Dashboard interativo com Dash/Plotly.**

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Como Executar](#-como-executar)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [API Endpoints](#-api-endpoints)
- [Dashboard](#-dashboard)
- [Análises PySpark](#-análises-pyspark)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)
- [Contato](#-contato)

---

## 🎯 Sobre o Projeto

Este projeto é um **pipeline ETL completo** para processamento e análise de logs de acesso da NASA do mês de Julho de 1995. O dataset contém aproximadamente **3,4 milhões de registros** e é processado usando **PySpark** para análises escaláveis.

### Objetivos:
- ✅ Extrair dados de logs Apache (formato `.tsv`)
- ✅ Transformar e limpar dados usando PySpark
- ✅ Carregar dados no PostgreSQL
- ✅ Criar análises avançadas (Top IPs, Recursos, Detecção de Anomalias)
- ✅ Visualizar dados em dashboard interativo

---

## ✨ Funcionalidades

### 📥 **ETL Pipeline**
- Download automático do dataset via Kaggle API
- Parser robusto de logs Apache Common Log Format
- Ingestão em batch via API REST
- Armazenamento otimizado em PostgreSQL

### 🔥 **Análises PySpark**
- Estatísticas descritivas (total de logs, IPs únicos, bytes transferidos)
- Top 20 IPs mais ativos
- Top 20 recursos mais acessados
- Distribuição de métodos HTTP (GET, POST, HEAD, etc.)
- Análise de códigos de status HTTP (2xx, 3xx, 4xx, 5xx)
- **Detecção de IPs suspeitos** usando Z-score (possível DDoS/Brute Force)

### 📊 **Dashboard Interativo**
- KPIs em tempo real (Total de Logs, IPs Únicos, Total de Bytes)
- Tabelas paginadas com Top 20 IPs e Recursos
- Gráfico de pizza para métodos HTTP
- Gráfico de barras para status HTTP agrupados por categoria
- Tabela de IPs suspeitos detectados
- Botão de atualização em tempo real

### 🛠 **API REST**
- Endpoint de ingestão de logs (`POST /logs/ingest`)
- Endpoint de contagem (`GET /logs/count`)
- Endpoint de top IPs (`GET /logs/top-ips`)
- Health check (`GET /health`)

---

## 🏗 Arquitetura