
# If there are no other languages, just return basic statistics

## SETUP
# Take as input a PDF or TXT file - whether with text layer or not yet
# Set up upload functionality (button) and storage (what is max?)
# Have check boxes for options/parameters (check possible languages)
    - Check/uncheck possible languages
    - Force OCR or not (any way to know quality of OCR?)
    - Provide translation of non-English words?
# Confirm file has been uploaded - print message about the file. Say it will be
# deleted within 24 hours - no information will be saved

## OCR TASKS
# once the PDF is uploaded - then:
# Check to see whether it has text layer. If so, use this unless 'force' parameter is used
# If force parameter or no text layer, then:
# identify the language of the document
# Use this to OCR the document with Tesseract

## LANGUAGE TASKS
# Run language identification throughout the document
# Print statistics about the language of the document, length of document, etc
# identify all non-English words, ngrams, etc
# Save these to a txt file
# Translate them into English (if requested)
# Print report (will be included in TXT file)

## MODIFY UPLOADED PDF
# Use Fitz to find all of the non-English words/phrases
# Highlight them in the text layer, a different color per language
# Tell the user to click download button for modified PDF, plus TXT SUMMARY REPORT listing non-English phrases, etc