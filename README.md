# nhl_optimizer

Python program with an interactive tkinter UI that uses PuLP integer programming to produce optimal fantasy hockey lineups.
A fantasy hockey lineup contains a set of hockey players who score fantasy points based on real life performance.
Each player has a salary given by the fantasy site, in this case fanduel.com.
The goal of the game is to maximize the amount of points scored by the players in the lineup while staying under a given salary cap.
This program takes point projections from a known fantasy sports website (found in proj.csv) and uses these to create optimal lineups based on the constraints of the game.
