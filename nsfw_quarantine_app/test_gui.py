import sys
print(f"Python path: {sys.path}")
print(f"Python executable: {sys.executable}")

try:
    import PySimpleGUI as sg
    print("PySimpleGUI imported successfully!")
    print(f"PySimpleGUI version: {sg.__version__}")
except ImportError as e:
    print(f"Error importing PySimpleGUI: {e}")
