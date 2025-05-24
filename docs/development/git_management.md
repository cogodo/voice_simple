# Git Management Guide

## 📦 **What Should Be in Git**

### **Essential Code & Configuration**
- ✅ Source code (`backend/`, `frontend/lib/`)
- ✅ Configuration files (`pubspec.yaml`, `requirements.txt`)
- ✅ Build configurations (`android/`, `ios/` configs)
- ✅ Scripts (`scripts/`)
- ✅ Documentation (`README.md`, `docs/`)

### **Project Documentation**
- ✅ `README.md` - Main project documentation
- ✅ `docs/` - All project documentation
- ✅ Development artifacts (moved to `docs/development/`)

## 🚫 **What Should NOT Be in Git**

### **Build Artifacts & Dependencies**
- ❌ `build/` directories
- ❌ `node_modules/`, `venv/`
- ❌ `.dart_tool/`, `__pycache__/`
- ❌ Platform-specific build files

### **Environment & Secrets**
- ❌ `.env` files (contain API keys)
- ❌ `local.properties`
- ❌ IDE-specific files (`.vscode/`, `.idea/`)

### **Temporary Files**
- ❌ Generated audio files (`*.wav`, `*.mp3`)
- ❌ Temporary audio processing (`backend/temp_audio/`)
- ❌ Log files (`*.log`)

### **Migration Artifacts**
- ❌ `deprecated/` folder (temporary during restructuring)

## 🎯 **Best Practices**

### **Environment Files**
```bash
# Include in git
.env.example          # Template showing required variables

# Exclude from git  
.env                 # Contains actual API keys
```

### **Documentation Strategy**
```
docs/
├── development/     # Development process docs
├── api/            # API documentation
├── setup/          # Setup guides
└── architecture/   # Architecture docs
```

### **Cleaning Up After Migration**
Once migration is stable, remove:
```bash
rm -rf deprecated/
git add -A
git commit -m "Clean up migration artifacts"
```

## 🔧 **Current .gitignore Strategy**

Our `.gitignore` follows these principles:
1. **Exclude build artifacts** - Nothing generated should be tracked
2. **Exclude secrets** - No API keys or sensitive data
3. **Exclude temp files** - Nothing temporary or cache-related
4. **Exclude migration artifacts** - Deprecated files during restructuring
5. **Include documentation** - Moved development docs to proper location

This ensures a clean repository with only essential, source-controlled files. 