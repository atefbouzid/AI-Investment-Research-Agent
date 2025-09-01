# AI Investment Research Agent - Full Stack ML Platform

🚀 A comprehensive AI-powered investment research platform built with Next.js, FastAPI, and advanced ML models.

## Features

- **🤖 AI-Powered Analysis**: Advanced stock analysis using Large Language Models
- **📊 Beautiful Dashboard**: Modern, responsive web interface
- **📈 Real-time Data**: Live stock data collection and analysis
- **📄 PDF Reports**: Automated LaTeX-generated investment reports
- **🔐 Secure Authentication**: JWT-based user authentication
- **⚡ Fast API**: High-performance FastAPI backend
- **🎨 Modern UI**: Beautiful Tailwind CSS interface

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Option 1: One-Command Startup (Recommended)

```bash
python start_project.py
```

This will automatically:
- Check dependencies
- Install frontend packages
- Start both backend and frontend servers
- Display access URLs and demo credentials

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python start_backend.py
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Demo Credentials

- **Username**: admin
- **Password**: admin

## Project Structure

```
AI-Investment-Research-Agent-Full-Stack-ML-Platform/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── auth/           # Authentication
│   │   ├── database/       # Database utilities
│   │   ├── models/         # Data models
│   │   └── services/       # Business logic
│   ├── reports/            # Generated reports
│   ├── main.py            # FastAPI application
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── app/               # App router pages
│   ├── components/        # Reusable components
│   ├── contexts/          # React contexts
│   └── package.json       # Node.js dependencies
├── database/              # Database schema
└── start_project.py       # One-command startup script
```

## Usage

1. **Login**: Use admin/admin to access the platform
2. **Analysis**: Enter a stock ticker (e.g., AAPL, TSLA) in the Analysis page
3. **Reports**: View and download generated PDF reports
4. **Dashboard**: Monitor your analysis history and statistics

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=investment_db
DB_USER=postgres
DB_PASSWORD=admin

# Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production

# AI Models
OPENROUTER_API_KEY=your_openrouter_api_key_here
NEWS_API_KEY=your_news_api_key_here

# Application Settings
DEBUG=true
LOG_LEVEL=info
```

## Features in Detail

### Stock Analysis
- Real-time data collection from multiple sources
- AI-powered sentiment analysis
- Technical and fundamental analysis
- Risk assessment and recommendations

### Report Generation
- Professional LaTeX-generated PDF reports
- Comprehensive analysis sections
- Charts and visualizations
- Download and sharing capabilities

### User Interface
- Responsive design for all devices
- Dark/light theme support
- Real-time updates
- Intuitive navigation

## API Endpoints

- `POST /auth/login` - User authentication
- `POST /analyze` - Start stock analysis
- `GET /analysis/history` - Get analysis history
- `GET /reports` - List generated reports
- `GET /download/{filename}` - Download reports

## Technologies Used

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Database
- **JWT** - Authentication
- **yfinance** - Stock data
- **Transformers** - AI models
- **LaTeX** - Report generation

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Lucide Icons** - Icons
- **Recharts** - Data visualization

## Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Type Checking
```bash
cd frontend
npm run type-check
```

### Linting
```bash
cd frontend
npm run lint
```

## Troubleshooting

### Common Issues

1. **Port already in use**: Make sure ports 3000 and 8000 are available
2. **Dependencies not found**: Run `pip install -r requirements.txt` and `npm install`
3. **API connection issues**: Check if backend is running on port 8000

### Support

For issues and questions:
1. Check the troubleshooting section
2. Review the console logs
3. Ensure all dependencies are installed correctly

## License

This project is for educational and demonstration purposes.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

🚀 **Happy Investing!** Built with ❤️ for AI-powered financial analysis.