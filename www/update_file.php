<?

  function read_file($file_name='/mnt/ram/led_settings.dict'){
    $file = fopen($file_name, "r");
    $output = fread($file, filesize($file_name));
    fclose($file);
    return $output;
  }

  $json = json_decode(read_file(), true);
  $output = $json;
  $file = fopen("/mnt/ram/led_settings.dict", "w");
  $post_html = $_POST;

  if( array_key_exists('pattern_speed', $post_html)){
    $output['pattern_speed'] = $post_html['pattern_speed'];
  }else{
    $output['pattern_speed'] = $json['pattern_speed'];
  }

  if (array_key_exists('color_speed', $post_html)){
    $output['color_speed'] = $post_html['color_speed'];
  }else{
    $output['color_speed'] = $json['color_speed'];
  }

  if (array_key_exists('sat_speed', $post_html)){
    $output['sat_speed'] = $post_html['sat_speed'];
  }else{
    $output['sat_speed'] = $json['sat_speed'];
  }

  if (array_key_exists('bright_slider', $post_html)){
    $output['bright_slider'] = $post_html['bright_slider'];
  }else{
    $output['bright_slider'] = $json['bright_slider'];
  }

  if (array_key_exists('color_button', $post_html)){
    if ($post_html['color_button'] == 'black'){
      $output['r'] = 0;
      $output['g'] = 0;
      $output['b'] = 0;
      $output['color_button'] = 'black';
    }
    elseif ($post_html['color_button'] == 'white'){
      $output['r'] = 175;
      $output['g'] = 175;
      $output['b'] = 175;
      $output['color_button'] = 'white';
    }
    elseif ($post_html['color_button'] == 'rainbow'){
      $output['color_button'] = 'rainbow';
    }
    elseif ($post_html['color_button'] == 'spectrum'){
      $output['color_button'] = 'solid';
    }


    # Patterns
    elseif ($post_html['color_button'] == 'FadeTail'){
      $output['pattern'] = 4;
    }
    elseif ($post_html['color_button'] == 'Fader'){
      $output['pattern'] = 3;
    }
    elseif ($post_html['color_button'] == 'SingleTail'){
      $output['pattern'] = 5;
    }
    elseif ($post_html['color_button'] == 'Sequence'){
      $output['pattern'] = 7;
    }
  }

  elseif (array_key_exists('color_value', $post_html)){
    $value = str_replace('#', '', $post_html['color_value']);
    $output['g'] = hexdec(sprintf("%s%s", $value[0], $value[1]));
    $output['r'] = hexdec(sprintf("%s%s", $value[2], $value[3]));
    $output['b'] = hexdec(sprintf("%s%s", $value[4], $value[5]));
    $output['color_button'] = 'solid';
  }
  else
  {
    $output['color_button'] = $json['color_button'];
    $output['pattern'] = $json['pattern'];
  }

  $output['html'] = $post_html;
  fwrite($file, json_encode($output));
  fwrite($file, "\n");
  fclose($file);
?>
