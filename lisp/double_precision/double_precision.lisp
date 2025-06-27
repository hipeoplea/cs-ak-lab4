(var ptr 0)
(var end 0)

(defunc add64 (a_lo a_hi b_lo b_hi) (
    (var sum_lo 0)
    (var sum_hi 0)
    (var carry 0)

    (set sum_lo (+ a_lo b_lo))

    (if (< sum_lo a_lo)
        (set carry 1)
        (set carry 0)
    )

    (set sum_hi (+ (+ a_hi b_hi) carry))

    (set sum_lo (+ (+ sum_lo a_lo) b_lo))

    (if (< sum_lo a_lo)
        (set carry 1)
        (set carry 0)
    )

    (set sum_hi (+ (+ (+ sum_hi a_hi) b_hi) carry))

    (print_string sum_hi)
    (print_string sum_lo)
))

(funcall add64 (2147483647) (1) (2147483647) (2))
