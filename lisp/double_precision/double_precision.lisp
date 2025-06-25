(var lo 0)
(var hi 0)
(var i 1)
(var square 0)
(var sum_lo 0)
(var sum_hi 0)

(defunc add64 (a_lo a_hi b_lo b_hi) (
  (var r_lo 0)
  (var r_hi 0)
  (set r_lo (+ a_lo b_lo))
  (set r_hi (+ a_hi b_hi))
  (if (< r_lo a_lo)
      (set r_hi (+ r_hi 1))
      0)
  (var pair [2])
  (set (get pair 0) r_lo)
  (set (get pair 1) r_hi)
  (return pair)
))

(while (< i 100001) (
  (set square (* i i))
  (set lo square)
  (set hi 0)

  (var result [2])
  (set result (funcall add64 sum_lo sum_hi lo hi))
  (set sum_lo (get result 0))
  (set sum_hi (get result 1))

  (set i (+ i 1))
))

(print_string "Sum hi = ")
(print_string sum_hi)
(print_string "
Sum lo = ")
(print_string sum_lo)
(print_string "
")
