(var i 1)
(var sum 0)
(var sum_sq 0)
(var tmp 0)

(while (< i 101) (
  (set sum (+ sum i))
  (set tmp (* i i))
  (set sum_sq (+ sum_sq tmp))
  (set i (+ i 1))
))

(set tmp (* sum sum))
(set tmp (- tmp sum_sq))

(print_string "Difference = ")
(print_string tmp)
(print_string "
")
