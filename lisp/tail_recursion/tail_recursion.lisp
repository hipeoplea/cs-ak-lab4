(defunc tail_recursion_loop (i) (
    (var char 0)
    (set char (+ i 48))
    (print_string char)
    (print_string "10")
    (set i (- i 1))
    (if (= i 0) (0) (funcall tail_recursion_loop (i)))
))
(funcall tail_recursion_loop (9))
