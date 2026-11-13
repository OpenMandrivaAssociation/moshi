Name:		moshi
Version:	1.15.2
Release:	2
Summary:	JSON library for Java and Kotlin
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/square/moshi
# Tag 1.15.2 (7f957b18ea123b7bb2ffc9d3c079e680eecf15e1). JVM main
# sources only. The Java 16 record adapter is installed as an MRJAR.
# Cooker okio 3.6.0 provides the okio types this release calls.
Source0:	moshi-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-21-openjdk-devel
BuildRequires:	kotlin = 2.0.21
BuildRequires:	kotlin-libs = 2.0.21
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(com.squareup.okio:okio)
BuildRequires:	mvn(com.google.code.findbugs:jsr305)

%description
com.squareup.moshi:moshi %{version}. JsonAdapter for Java classes and
records. The upstream build is Gradle. This package compiles the JVM
sources with javac and the installed kotlinc.

%package kotlin
Summary:	Kotlin reflection adapter for Moshi
Group:		Development/Java
Requires:	moshi = %{EVRD}
Requires:	mvn(org.jetbrains.kotlin:kotlin-stdlib)

%description kotlin
com.squareup.moshi:moshi-kotlin %{version}. KotlinJsonAdapterFactory
reads and writes Kotlin classes through kotlin-reflect.

%package adapters
Summary:	Extra JsonAdapters for Moshi
Group:		Development/Java
Requires:	moshi = %{EVRD}

%description adapters
com.squareup.moshi:moshi-adapters %{version}. PolymorphicJsonAdapterFactory
and the RFC 3339 date adapter.

%prep
%autosetup -n moshi-%{version}
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
test -s LICENSE.txt
test -s moshi/src/main/java/com/squareup/moshi/Moshi.java
test -s moshi/src/main/java16/com/squareup/moshi/RecordJsonAdapter.java
test -s moshi/src/main/java/com/squareup/moshi/-MoshiKotlinExtensions.kt
test -s moshi-kotlin/src/main/java/com/squareup/moshi/kotlin/reflect/KotlinJsonAdapter.kt
test -s moshi-adapters/src/main/java/com/squareup/moshi/adapters/PolymorphicJsonAdapterFactory.java

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
CP="%{_javadir}/okio.jar:%{_javadir}/javax.annotation.jar:%{_javadir}/kotlin-stdlib.jar:%{_javadir}/kotlin-reflect.jar"
mkdir -p classes classes16
find moshi/src/main/java -name '*.java' > java.list
test "$(wc -l < java.list)" -eq 31
javac --release 8 -encoding UTF-8 -cp "$CP" -d classes @java.list
javac --release 16 -encoding UTF-8 -cp "classes:$CP" -d classes16 \
	moshi/src/main/java16/com/squareup/moshi/RecordJsonAdapter.java
kotlinc -jvm-target 1.8 -language-version 2.0 -no-stdlib \
	-jdk-home "$JAVA_HOME" -J-Xmx2g \
	-cp "classes:$CP" \
	-d classes \
	moshi/src/main/java/com/squareup/moshi/-MoshiKotlinExtensions.kt \
	moshi/src/main/java/com/squareup/moshi/-MoshiKotlinTypesExtensions.kt
mkdir -p mr/META-INF/versions/16
/bin/cp -a classes/. mr/
/bin/cp -a classes16/. mr/META-INF/versions/16/
printf 'Manifest-Version: 1.0\nMulti-Release: true\nAutomatic-Module-Name: com.squareup.moshi\n\n' > manifest.mf
jar cfm moshi.jar manifest.mf -C mr .
jar i moshi.jar
jar tf moshi.jar | grep -F -q 'META-INF/versions/16/com/squareup/moshi/RecordJsonAdapter$ComponentBinding.class'
mkdir -p ktclasses
kotlinc -jvm-target 1.8 -language-version 2.0 -no-stdlib \
	-jdk-home "$JAVA_HOME" -J-Xmx2g \
	-cp "moshi.jar:$CP" \
	-d ktclasses \
	moshi-kotlin/src/main/java/com/squareup/moshi/kotlin/reflect/KotlinJsonAdapter.kt \
	moshi-kotlin/src/main/java/com/squareup/moshi/KotlinJsonAdapter.kt
jar cf moshi-kotlin.jar -C ktclasses .
jar i moshi-kotlin.jar
mkdir -p adclasses
find moshi-adapters/src/main/java -name '*.java' > adapters.list
test "$(wc -l < adapters.list)" -eq 5
javac --release 8 -encoding UTF-8 -cp "moshi.jar:$CP" -d adclasses @adapters.list
jar cf moshi-adapters.jar -C adclasses .
jar i moshi-adapters.jar
test -s moshi.jar
test -s moshi-kotlin.jar
test -s moshi-adapters.jar

cat > moshi.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.squareup.moshi</groupId>
  <artifactId>moshi</artifactId>
  <version>%{version}</version>
  <name>Moshi</name>
  <description>A modern JSON library for Android, Java and Kotlin.</description>
  <url>https://github.com/square/moshi</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.squareup.okio</groupId>
      <artifactId>okio</artifactId>
      <version>3.6.0</version>
    </dependency>
    <dependency>
      <groupId>com.google.code.findbugs</groupId>
      <artifactId>jsr305</artifactId>
      <version>3.0.2</version>
    </dependency>
    <dependency>
      <groupId>org.jetbrains.kotlin</groupId>
      <artifactId>kotlin-stdlib</artifactId>
      <version>2.0.21</version>
    </dependency>
  </dependencies>
</project>
END

cat > moshi-kotlin.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.squareup.moshi</groupId>
  <artifactId>moshi-kotlin</artifactId>
  <version>%{version}</version>
  <name>Moshi Kotlin</name>
  <description>Kotlin reflection adapter for Moshi.</description>
  <url>https://github.com/square/moshi</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.squareup.moshi</groupId>
      <artifactId>moshi</artifactId>
      <version>%{version}</version>
    </dependency>
    <dependency>
      <groupId>org.jetbrains.kotlin</groupId>
      <artifactId>kotlin-reflect</artifactId>
      <version>2.0.21</version>
    </dependency>
  </dependencies>
</project>
END

cat > moshi-adapters.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.squareup.moshi</groupId>
  <artifactId>moshi-adapters</artifactId>
  <version>%{version}</version>
  <name>Moshi Adapters</name>
  <description>Extra JsonAdapters for Moshi.</description>
  <url>https://github.com/square/moshi</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.squareup.moshi</groupId>
      <artifactId>moshi</artifactId>
      <version>%{version}</version>
    </dependency>
    <dependency>
      <groupId>com.google.code.findbugs</groupId>
      <artifactId>jsr305</artifactId>
      <version>3.0.2</version>
    </dependency>
  </dependencies>
</project>
END

%install
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
mkdir -p %{buildroot}
sysjar install --buildroot %{buildroot} \
	--artifact moshi.pom:moshi.jar \
	--file-name moshi \
	--filelist moshi.list
sysjar install --buildroot %{buildroot} \
	--artifact moshi-kotlin.pom:moshi-kotlin.jar \
	--file-name moshi-kotlin \
	--filelist kotlin.list
grep -F -q '%%dir /usr/share/sysjar/index/com.squareup.moshi' moshi.list
grep -F -q '%%dir /usr/share/sysjar/index/com.squareup.moshi' kotlin.list
sysjar install --buildroot %{buildroot} \
	--artifact moshi-adapters.pom:moshi-adapters.jar \
	--file-name moshi-adapters \
	--filelist adapters.list
grep -v -F '%%dir /usr/share/sysjar/index/com.squareup.moshi' kotlin.list > kotlin.files
grep -v -F '%%dir /usr/share/sysjar/index/com.squareup.moshi' adapters.list > adapters.files
if grep -F -q '%%dir /usr/share/sysjar/index/com.squareup.moshi' kotlin.files; then
	exit 1
fi
if grep -F -q '%%dir /usr/share/sysjar/index/com.squareup.moshi' adapters.files; then
	exit 1
fi
/bin/cp moshi.list moshi.files

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
MOSHI=%{buildroot}%{_javadir}/moshi.jar
KOTLIN=%{buildroot}%{_javadir}/moshi-kotlin.jar
ADAPTERS=%{buildroot}%{_javadir}/moshi-adapters.jar
test -s "$MOSHI"
test -s "$KOTLIN"
test -s "$ADAPTERS"
CP="$MOSHI:%{_javadir}/okio.jar:%{_javadir}/javax.annotation.jar:%{_javadir}/kotlin-stdlib.jar:%{_javadir}/kotlin-reflect.jar"
mkdir -p check
cat > check/MoshiCheck.java << 'EOF'
import com.squareup.moshi.JsonAdapter;
import com.squareup.moshi.Moshi;
public class MoshiCheck {
	public record Point(int x, int y) {}
	public static void main(String[] args) throws Exception {
		Moshi moshi = new Moshi.Builder().build();
		JsonAdapter<String> strings = moshi.adapter(String.class);
		if (!"\"moshi\"".equals(strings.toJson("moshi"))) {
			throw new RuntimeException(strings.toJson("moshi"));
		}
		JsonAdapter<Point> points = moshi.adapter(Point.class);
		Point back = points.fromJson(points.toJson(new Point(2, 4)));
		if (back.x() != 2 || back.y() != 4) {
			throw new RuntimeException(String.valueOf(back));
		}
		System.out.println("moshi_ok " + points.toJson(back));
	}
}
EOF
javac --release 16 -encoding UTF-8 -cp "$CP" -d check check/MoshiCheck.java
java -cp "check:$CP" MoshiCheck > check/moshi.log
cat check/moshi.log
grep -F -qx 'moshi_ok {"x":2,"y":4}' check/moshi.log
cat > check/MoshiProbe.kt << 'EOF'
data class MoshiProbe(val n: Int)
EOF
kotlinc -jvm-target 1.8 -language-version 2.0 -no-stdlib \
	-jdk-home "$JAVA_HOME" \
	-cp "%{_javadir}/kotlin-stdlib.jar" \
	-d check check/MoshiProbe.kt
cat > check/MoshiKotlinCheck.java << 'EOF'
import com.squareup.moshi.JsonAdapter;
import com.squareup.moshi.Moshi;
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory;
public class MoshiKotlinCheck {
	public static void main(String[] args) throws Exception {
		Moshi moshi = new Moshi.Builder().add(new KotlinJsonAdapterFactory()).build();
		JsonAdapter<MoshiProbe> adapter = moshi.adapter(MoshiProbe.class);
		MoshiProbe back = adapter.fromJson("{\"n\":7}");
		if (back.getN() != 7) {
			throw new RuntimeException("n=" + back.getN());
		}
		String json = adapter.toJson(new MoshiProbe(7));
		if (!json.contains("\"n\":7") && !json.contains("\"n\": 7")) {
			throw new RuntimeException(json);
		}
		System.out.println("moshi_kotlin_ok " + json);
	}
}
EOF
javac --release 8 -encoding UTF-8 -cp "check:$KOTLIN:$CP" -d check check/MoshiKotlinCheck.java
java -cp "check:$KOTLIN:$CP" MoshiKotlinCheck > check/kotlin.log
cat check/kotlin.log
grep -F -qx 'moshi_kotlin_ok {"n":7}' check/kotlin.log
cat > check/AdapterCheck.java << 'EOF'
import com.squareup.moshi.JsonAdapter;
import com.squareup.moshi.Moshi;
import com.squareup.moshi.adapters.PolymorphicJsonAdapterFactory;
public class AdapterCheck {
	public static class Pet {
		public String name;
	}
	public static class Dog extends Pet {}
	public static void main(String[] args) throws Exception {
		Moshi moshi = new Moshi.Builder()
			.add(PolymorphicJsonAdapterFactory.of(Pet.class, "type").withSubtype(Dog.class, "dog"))
			.build();
		JsonAdapter<Pet> adapter = moshi.adapter(Pet.class);
		Dog dog = new Dog();
		dog.name = "ada";
		String json = adapter.toJson(dog);
		Pet back = adapter.fromJson(json);
		if (!(back instanceof Dog) || !"ada".equals(back.name)) {
			throw new RuntimeException(json);
		}
		System.out.println("moshi_adapters_ok " + json);
	}
}
EOF
javac --release 8 -encoding UTF-8 -cp "check:$ADAPTERS:$CP" -d check check/AdapterCheck.java
java -cp "check:$ADAPTERS:$CP" AdapterCheck > check/adapters.log
cat check/adapters.log
grep -F -qx 'moshi_adapters_ok {"type":"dog","name":"ada"}' check/adapters.log

%files -f moshi.files
%license LICENSE.txt
%doc README.md

%files kotlin -f kotlin.files

%files adapters -f adapters.files
