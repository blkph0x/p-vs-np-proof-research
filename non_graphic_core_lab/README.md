# Non-graphic core adversary

This lab supplies the next hard-frontier control after the easy graphic
family: small binary matroids that contain an explicit Fano restriction,
therefore are non-graphic, while exhaustive cuts certify internal
4-connectivity and a large balanced-cut connectivity value.

Run:

```text
python -m unittest -v test_non_graphic_core.py
python run_experiments.py
python INDEPENDENT_REVIEW.py
```

The matrices are finite controls. The Fano restriction proves non-graphicness;
the cut audit proves the stated connectivity only for the saved matrices. A
high trellis width still does not by itself prove minimum-distance hardness or
resolve P versus NP.
