# -*- coding: utf-8 -*-
"""The MTRESS flavour of the solph Model.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

from oemof import solph


class Model(solph.Model):
    def solve(
        self,
        solver="highs",
        solver_io="lp",
        allow_nonoptimal=False,
        solve_kwargs=None,
        cmdline_options=None,
    ):
        return super().solve(
            solver=solver,
            solver_io=solver_io,
            allow_nonoptimal=allow_nonoptimal,
            solve_kwargs=solve_kwargs,
            cmdline_options=cmdline_options,
        )
