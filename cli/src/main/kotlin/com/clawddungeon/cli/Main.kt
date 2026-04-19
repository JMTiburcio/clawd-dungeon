package com.clawddungeon.cli

fun main(args: Array<String>) {
    when (args.firstOrNull()) {
        "train"   -> runTrain()
        "watch"   -> runWatch()
        "balance" -> runBalance()
        else -> {
            println("Usage:")
            println("  ./gradlew :cli:run --args=\"train\"")
            println("  ./gradlew :cli:run --args=\"watch\"")
            println("  ./gradlew :cli:run --args=\"balance\"")
        }
    }
}
