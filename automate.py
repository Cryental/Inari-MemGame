import cv2
import numpy as np
import pyautogui
import keyboard
import time
from PIL import Image
import imagehash

def find_cards(image):
    """Detects card contours in an image, returning sorted bounding boxes."""
    # Instead of converting to grayscale, use the max value across the BGR channels
    max_channel = np.max(image, axis=2)
    _, thresh = cv2.threshold(max_channel, 240, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Assume the cards are the larger contours found
    card_rects = [cv2.boundingRect(cnt) for cnt in contours if cv2.contourArea(cnt) > 5000]
    # Sort the bounding boxes by y first, then by x (top-to-bottom, then left-to-right)
    card_rects.sort(key=lambda x: (x[1], x[0]))
    return card_rects

def calculate_phash(image):
    """Calculates the perceptual hash of a card image."""
    pil_image = Image.fromarray(image)
    return imagehash.phash(pil_image)

def calculate_average_color(image, x, y, w, h):
    """Calculates the average color of a card image."""
    card_image = image[y:y+h, x:x+w]
    average_color_per_row = np.average(card_image, axis=0)
    average_color = np.average(average_color_per_row, axis=0)
    return average_color

def find_matching_pairs(cards, image):
    """Identifies matching pairs of cards based on perceptual hash and color."""
    hashes = [calculate_phash(image[y:y+h, x:x+w]) for x, y, w, h in cards]
    colors = [calculate_average_color(image, x, y, w, h) for x, y, w, h in cards]
    matched = set()
    pairs = []

    for i in range(len(cards)):
        if i in matched:
            continue
        min_diff = float('inf')
        min_color_diff = float('inf')
        pair_index = -1
        for j in range(len(cards)):
            if i != j and j not in matched:
                # Calculate hash difference
                hash_diff = hashes[i] - hashes[j]
                # Calculate color difference
                color_diff = np.linalg.norm(np.array(colors[i]) - np.array(colors[j]))
                # Check if this is the smallest difference found so far
                if hash_diff < min_diff or (hash_diff == min_diff and color_diff < min_color_diff):
                    min_diff = hash_diff
                    min_color_diff = color_diff
                    pair_index = j
        # If a pair is found with a difference below the thresholds, add to pairs
        if pair_index != -1 and min_diff <= 20 and min_color_diff <= 15:  # Adjust color threshold based on testing
            pairs.append((cards[i], cards[pair_index]))
            matched.update([i, pair_index])

    return pairs


def click_center(x, y, w, h):
    """Clicks at the center of a given rectangle."""
    pyautogui.click(x + w//2, y + h//2)

def automate_game():
    """Main automation function triggered by key presses."""
    image = None
    while True:
        if keyboard.is_pressed('0'):
            screenshot = pyautogui.screenshot()
            image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            cards = find_cards(image)
            print('Cards have been captured and stored in memory.')
            time.sleep(1)  # Prevent rapid re-activation

        elif keyboard.is_pressed('1') and image is not None:
            matching_pairs = find_matching_pairs(cards, image)
            for card1, card2 in matching_pairs:
                click_center(*card1)
                time.sleep(0.3)
                click_center(*card2)
                time.sleep(0.3)
            print('Clicked on all matching pairs.')
            break

automate_game()
