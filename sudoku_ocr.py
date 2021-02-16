""" Sudoku OCR class
- takes as an input a sudoku puzzle picture file or a vido stream
- after 'locking' the the sudoku board grid on the input image
- it analyses each cell of the board and returns the board definition
- in the form of a list consisting of '.' (empty cell), '1', '2', etc.
"""

import sys
import pickle
import cv2
import numpy as np
import imutils
from imutils.perspective import four_point_transform
from skimage.segmentation import clear_border
from display import error_message


class SudokuOCR:
    """ Sudoku OCR engine that allows recognition of sudoku puzzle boards
    in images (files or video streams)
    The class uses pre-trained neural network to classify defined sudoku clues

    TODO:
     - (optionally) allow selection of neural network digit classifier
     - (important) check the active camera port number
    """

    def __init__(self, img_fname=None, cnn_classifier="./cnn_models/neuralNetMLP.pkl"):
        self.image = cv2.imread(img_fname, cv2.IMREAD_UNCHANGED) if img_fname else None
        self.window_name = "Sudoku"
        with open(cnn_classifier, 'rb') as solver:      # TODO - optional
            self.cnn = pickle.load(solver)
        if self.image is None:
            self.camera = cv2.VideoCapture(2)           # TODO - important!
            if not self.camera.isOpened():
                self.camera.open()
        else:
            self.camera = None

    def _find_board(self):
        """ locate and return the sudoku board picture """
        # convert the image to grayscale and blur it slightly,
        # then apply adaptive thresholding with inversion
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 1.5)
        threshold = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY_INV, 11, 2)

        # find contours in the image and sort them by size in descending order
        contours = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        # find polygon contour that corresponds to the puzzle outline
        for cnt in contours:
            puzzle_contour = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            if len(puzzle_contour) == 4:
                break
        else:
            return None

        # when using video: set minimum relative area of of the sudoku contour
        # to increase probability of correctly classifying the board clues
        tot_area = self.image.shape[0] * self.image.shape[1]
        min_area = 0.2 if self.camera is None else 0.45
        if (0.95 > cv2.contourArea(puzzle_contour) / tot_area > min_area
                and not self._touches_image_boundary(puzzle_contour)):
            cv2.drawContours(self.image, [puzzle_contour], -1, (0, 255, 0), 2)
            return four_point_transform(threshold, puzzle_contour.reshape(4, 2))

        return None

    def _touches_image_boundary(self, contour):
        """ check if the contour touches image boundary """
        max_y, max_x, _ = self.image.shape
        on_edge = list()
        for i in range(4):
            on_edge.append(bool(contour[i, 0, 0] == 0 or contour[i, 0, 0] == max_x - 1))
            on_edge.append(bool(contour[i, 0, 1] == 0 or contour[i, 0, 1] == max_y - 1))
        return any(on_edge)

    def _extract_digit(self, cell):
        """ classify digit in the cell or return '0' if the cell is empty """
        # the border width (5) was found 'experimentally' as a compromise
        # between removing the noise related to sudoku lines and cutting the actual digits
        cell = clear_border(cell, 5)
        contours = cv2.findContours(cell.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        if len(contours) == 0:
            return '0'

        mask = np.zeros(cell.shape, dtype="uint8")
        cv2.drawContours(mask, [contours[0]], -1, 255, -1)

        # compute the percentage of masked pixels relative to the total area of the image
        # if less than 8% of the mask is filled then we are looking at
        # noise and can safely ignore the contour ('1' usually occupy > 12%)
        cell_h, cell_w = cell.shape
        if cv2.countNonZero(mask) / float(cell_w * cell_h) < 0.08:
            return '0'
        cell = cv2.bitwise_and(cell, cell, mask=mask)

        # based on comparing proportions between actual digit size vs. margins
        # for the training set and typical sudoku cells (done outside of this app)
        # we select 46x46 rectangle centered around the digit out of the 60x60 'digit' image
        # and only then resize it to 28x28 (size of the training set images)
        x_1, y_1, rect_w, rect_h = cv2.boundingRect(contours[0])
        x_start = min(max(round(x_1 - (46 - rect_w) / 2), 0), 14)
        y_start = min(max(round(y_1 - (46 - rect_h) / 2), 0), 14)
        x_end = x_start + 46
        y_end = y_start + 46
        cell = cell[y_start:y_end, x_start:x_end]
        clues = np.ndarray(784, dtype=np.uint8).reshape(1, 784)
        clues[0] = cv2.resize(cell, (28, 28)).reshape(784)

        return str(self.cnn.predict(clues)[0])

    def show_contour(self, time=500):
        """ show the latest camera captured image with contour """
        cv2.imshow(self.window_name, self.image)
        cv2.waitKey(time)

    def close(self):
        """ Release the camera and close all display windows"""
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()

    def sudoku_ocr(self):
        """ read or capture the sudoku board image,
         extract and classify digits, return the sudoku puzzle definition board """

        if self.image is not None:
            self.image = imutils.resize(self.image, width=630)
            birds_eye_view = self._find_board()
        else:
            while True:
                if cv2.waitKey(10) & 0xFF == ord('q'):
                    break
                _, self.image = self.camera.read()
                cv2.imshow(self.window_name, self.image)
                self.image = imutils.resize(self.image, width=630)
                birds_eye_view = self._find_board()
                if birds_eye_view is not None:
                    break

        if birds_eye_view is None:
            error_message('contour_not_found', None, additional_info=" ")
            sys.exit(-1)

        birds_eye_view = cv2.resize(birds_eye_view.copy(), (540, 540))
        board = []
        step_x = birds_eye_view.shape[1] / 9
        step_y = birds_eye_view.shape[0] / 9

        for row in range(9):
            for col in range(9):
                cell = birds_eye_view[round(row*step_y):round((row+1)*step_y),
                                      round(col*step_x):round((col+1)*step_x)]
                digit = self._extract_digit(cell)
                board.append(digit if digit != '0' else '.')

        return board
