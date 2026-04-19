plugins {
    kotlin("jvm")
    application
}

dependencies {
    implementation(project(":core"))
}

application {
    mainClass.set("com.clawddungeon.cli.MainKt")
}
