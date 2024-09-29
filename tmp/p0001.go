package main

import "fmt"

func add(a, b int) int {
    return a + b
}

func main() {
	var a, b int
	fmt.Scanf("%d %d", &a, &b)
	fmt.Printf("%d", add(a, b))
}
