# There is no runtime or added struct to represent the length of an array,
# So, this is a quick and dirty way to calculate the length.
END_OF_ARRAY = -99999
fn len(A)
  if A[0] = END_OF_ARRAY
    0
  else
    1 + len(A + 1)
  end
end

fn abs(x)
  if x < 0
    -x
  else
    x
  end
end

fn sign(x)
  if x < 0
    -1
  else
    1
  end
end

fn min(a, b)
  if a > b
    b
  else
    a
  end
end

fn make_2d(x, y)
  X = malloc(x)
  __make_2d__(x, y, X)
  X
end
fn __make_2d__(x, y, X)
  if x > 0
    X[0] = malloc(y)
    __make_2d__(x - 1, y, X + 1)
  end
end

# since heap is unmanaged, this is a dumb implementation of malloc to use heap.
# this will only grow and there is no free.
heap_free_offset = 0
fn malloc(size)
   start = _sections[3] + heap_free_offset
   heap_free_offset = heap_free_offset + size
   start
end

# Straight forward approach
R = 0  D = 1  U = 2  L = 3
fn solve_day3(A, space)
  l = len(A)

  if l = 0
    min_dist(space, 0, 0)
  else
    next_coord = draw(0, 0, A, space)
    solve_day3(next_coord[0], next_coord[1], A + 2, space)
  end
end

fn draw(x, y, A, space)
  d = A[0]
  l = A[1]

  if d = R
     x_next = x + l
     draw_x(space, x, x_next, y)
     x_new = x_next
  else
    if d = L
      x_next = x - l
      draw_x(space, x, x_next, y)
      x_new = x_next
    else
      if d = D
        y_next = y - l
        draw_y(space, x, y, y_next)
        y_new = y_next
      else
        y_next = y + l
        draw_y(space, x, y, y_next)
        y_new = y_next
      end
    end
  end

  coord = malloc(2)
  coord[0] = x_new
  coord[1] = y_new
  coord
end

fn draw_x(space, x0, x1, y)
  incr = sign(x1 - x0)
  space[x0][y] = space[x0][y] + 1
  if x0 != x1
    draw_x(space, x0 + incr, x1, y)
  end
end

fn draw_y(space, x, y0, y1)
  incr = sign(y1 - y0)
  space[x][y0] = space[x][y0] + 1
  if y0 != y1
    draw_y(space, x, y0 + incr, y1)
  end
end

# The above drawer functions drew the heat map of points occupied.
# min_dist minimizes m((0,0), (x, y)) for each (x, y) pair in space
max_dist = 999999
fn min_dist(space, x, y)
  if space[x][y] > 1 and x < 2000 and y < 2000
    a = x + y
  else
    a = max_dist
  end

  b = min_dist(space, x + 1, y)
  c = min_dist(space, x, y + 1)
  d = min_dist(space, x + 1, y + 1)

  min(min(a, b), min(c, d))
end

fn main()
   space = make_2d(2000, 2000)
   # The answer should be 159 for the below input.
   input = [
     R,75,D,30,R,83,U,83,L,12,D,49,R,71,U,7,L,72,U,62,R,66,U,55,R,34,D,71,R,55,D,58,R,83,
     END_OF_ARRAY
   ]

   print(space[0])
   #print(solve_day3(input, space))
end
