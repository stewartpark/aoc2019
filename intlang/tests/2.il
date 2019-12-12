fn bool(x)
  if x
    1
  else
    0
  end
end

fn main()
  print(bool(1 > 0))
  print(bool(0 > 1))

  print(bool(1 < 0))
  print(bool(0 < 1))

  print(bool(1 >= 0))
  print(bool(0 >= 1))

  print(bool(1 <= 0))
  print(bool(0 <= 0))

  print(bool(1 = 1))
  print(bool(1 = 0))
  print(bool(0 = 1))

  print(bool(1 != 1))
  print(bool(1 != 0))
end
