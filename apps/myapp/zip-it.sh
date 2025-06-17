#!/bin/bash

# Usage: ./zip-it.sh preedit|da|sonnet

case "$1" in
  preedit)
    ZIPFILE="accessible-outings_preedit.zip"
    ;;
  da)
    ZIPFILE="accessible-outings_DA_postedit.zip"
    ;;
  sonnet)
    ZIPFILE="accessible-outings_Sonnet_postedit.zip"
    ;;
  *)
    echo "Usage: $0 {preedit|da|sonnet}"
    exit 1
    ;;
esac

zip -r "$ZIPFILE" . -x ".venv/*" ".venv" ".git/*" ".git" "*/__pycache__/*" "__pycache__" "zip-it.sh" ".env" "Suggestions.txt" "simple_unit_test.py"
