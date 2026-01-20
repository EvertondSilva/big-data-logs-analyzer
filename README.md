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

Componentes:
Kaggle API: Download automático do dataset
ETL Download: Script Python para baixar dados
Data Files: Arquivos .tsv (3.4M registros)
ETL Load: Parser e carga em batch
FastAPI: API REST (porta 8002)
PostgreSQL: Banco de dados principal
PySpark Analysis: Processamento distribuído
Dashboard: Visualização interativa (porta 8050)
Analysis Tables: Resultados das análises

---

## 🛠 Tecnologias Utilizadas

### **Backend & Data Processing**
- **Python 3.11** - Linguagem principal
- **PySpark 3.5.0** - Processamento distribuído de dados
- **FastAPI** - API REST de alta performance
- **PostgreSQL 15** - Banco de dados relacional
- **SQLAlchemy** - ORM e conexões de banco
- **Pandas** - Manipulação de dados

### **Frontend & Visualização**
- **Dash 2.14.2** - Framework para dashboards interativos
- **Plotly** - Biblioteca de gráficos interativos

### **DevOps & Infra**
- **Docker & Docker Compose** - Containerização
- **Kaggle API** - Download automático de datasets

### **Outras**
- **python-dotenv** - Gerenciamento de variáveis de ambiente
- **psycopg2** - Driver PostgreSQL

---

## 📦 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Docker** (versão 20.10+)
- **Docker Compose** (versão 2.0+)
- **Conta Kaggle** (para download do dataset)

---

## 🚀 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/nasa-etl-pipeline.git
cd nasa-etl-pipeline