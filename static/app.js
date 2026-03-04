//initialize variables
var socket = io();
var password = 0;
var uid = 0;
var buzzer = new Audio('static/buzzer.mp3') //buzzer sound file

function setMode(){
  if (desiredTemp >= (temp + 2)) {
      document.getElementById("desiredTempt").innerHTML = "Desired Temp: " + desiredTemp + "C (Heating)";
      document.getElementById("desiredTempt").style.left = "40.5%";
  } else if (desiredTemp <= (temp - 2)) {
      document.getElementById("desiredTempt").innerHTML = "Desired Temp: " + desiredTemp + "C (Cooling)";
      document.getElementById("desiredTempt").style.left = "40.5%";
  } else {
      document.getElementById("desiredTempt").innerHTML = "Desired Temp: " + desiredTemp + "C (Off)";
      document.getElementById("desiredTempt").style.left = "41.5%";
  }
}


function startTemp(id) {
  if (id == 98) {
      document.getElementById("key").innerHTML = "Welcome Sadeer";
      document.getElementById("key").style.left = "44%";
  } else if (id == 171) {
      document.getElementById("key").innerHTML = "Welcome Alhassan";
      document.getElementById("key").style.left = "43.5%";
  }
  document.getElementById("password").remove();
  document.getElementById("passkey").remove();
  document.getElementById("dht11").innerHTML = "Loading...";
  document.getElementById("desiredTempt").innerHTML = "Enter your Desired Temperature";
  document.getElementById("tempContent").innerHTML = "<input type='text' id ='desiredTemp'> <button class='desiredTemp' onclick='enterDesiredTemp()'>Enter</button>"
  socket.emit('startTemp');
}


socket.on('tempOut', function(weather) {
  tempOut = weather.tempOut;
  feelsLike = weather.feelsLike;
  climate = weather.climate;
  document.getElementById("weather").innerHTML = "Temperature Outside: " + tempOut + "C | Feels Like: " + feelsLike + "C | " + climate;
})


socket.on('dht11', function(dht11) {
  console.log(dht11.humidity + " " + dht11.temp)
  temp = dht11.temp;
  humidity = dht11.humidity;
  document.getElementById("dht11").style.left = "38.3%";
  document.getElementById("dht11").innerHTML = "Temperature: " + temp + "C | Humidity: " + humidity + "%";
})


socket.on('uid', function(uid) {
  console.log(uid)
  if (uid.uid == "98") {
      startTemp(uid.uid)
  } else if (uid.uid == "171") {
      startTemp(uid.uid)
  } else {
      document.getElementById("password").style.border = "2px solid red";
      socket.emit('invalid', {'invalid': 1 });
      buzzer.play();
  }
})


socket.on('checkTemp', function() {
  setMode() 
})


function enterPassword() {
  password = document.getElementById("password").value;
  if (password == "98") {
      startTemp(password)
  } else if (password == "171") {
      startTemp(password)
  } else {
      document.getElementById("password").style.border = "2px solid red";
      socket.emit('invalid', {'invalid': 1 });
      buzzer.play();
  }
}


function enterDesiredTemp() {
  desiredTemp = Number(document.getElementById("desiredTemp").value);
  if (desiredTemp > 0 && desiredTemp < 40) {
      document.getElementById("tempContent").innerHTML = "<button id='reset' class='reset' onclick='reset()'>Turn Off/New Desired Temperature</button>";
      socket.emit('desiredTemp', { 'desiredTemp': desiredTemp });
      setMode()
  } else {
      document.getElementById("desiredTemp").style.border = "2px solid red";
      socket.emit('invalid', {'invalid': 2 });
      buzzer.play();
  }
}


function reset() {
  location.reload();
  socket.emit('reset');
}