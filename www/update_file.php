<?

  function get_lock($file_name='/mnt/ram/.led_settings.lock'){
    while(file_exists($file_name)){
      time_nanosleep(0,10000000);
    }
    $fp = fopen($file_name, 'w');
    fwrite($fp, '');
    fclose($fp);
  }

  function release_lock($file_name='/mnt/ram/.led_settings.lock'){
    unlink($file_name);
  }

  function read_file($file_name='/mnt/ram/led_settings.dict',
                     $backup_file='/home/levi/funkytown_leds/led_settings.dict.default'){

    if(!file_exists($file_name)){
      copy($backup_file, $file_name);
    }
    get_lock();
    $output = file_get_contents($file_name);
    release_lock();
    return $output;
  }

  function write_file ($input) {
    get_lock();
    $file = fopen("/mnt/ram/led_settings.dict", "w");
    fwrite($file, json_encode($input));
    fflush($file);
    fclose($file);
    release_lock();
  }

  function build_json($input){
    $post_html = $_POST;
    $json = json_decode($input, true);

    // Pattern Slide
    if(array_key_exists('pattern_slider', $post_html)){
      $output['pattern_slider'] = $post_html['pattern_slider'];
    }else{
      $output['pattern_slider'] = $json['pattern_slider'];
    }

    // Color Slider
    if (array_key_exists('hue_slider', $post_html)){
      $val = doubleval($post_html['hue_slider']) * 0.0001;
      $val = abs(log(10, $val) - 1.24);
      $output['hue_slider'] = $val;
    }else{
      $output['hue_slider'] = $json['hue_slider'];
    }

    // Saturation Slider
    if (array_key_exists('saturation_slider', $post_html)){
      $output['saturation_slider'] = $post_html['saturation_slider'];
    }else{
      $output['saturation_slider'] = $json['saturation_slider'];
    }

    // Brightness Slider
    if (array_key_exists('brightness_slider', $post_html)){
      $output['brightness_slider'] = $post_html['brightness_slider'];
    }else{
      $output['brightness_slider'] = $json['brightness_slider'];
    }

    // Buttons
    if (array_key_exists('id', $post_html) && array_key_exists('value', $post_html)){
      // Color Buttons
      if ($post_html['id'] == 'color_button'){
        // Black
        if ($post_html['value'] == 'black'){
          $output['r'] = 0;
          $output['g'] = 0;
          $output['b'] = 0;
          $output['color_button'] = 'black';
        }
        // White
        elseif ($post_html['value'] == 'white'){
          $output['r'] = 175;
          $output['g'] = 175;
          $output['b'] = 175;
          $output['color_button'] = 'white';
        }
        // Rainbow
        elseif ($post_html['value'] == 'rainbow'){
          $output['color_button'] = 'rainbow';
        }
        // Spectrum
        elseif ($post_html['value'] == 'spectrum'){
          $output['color_button'] = 'solid';
        }
      } else {
        $output['color_button'] = $json['color_button'];
      }

      // Pattern Buttons
      if ($post_html['id'] == 'pattern_button'){
        // Fade Tail
        if ($post_html['value'] == 'FadeTail'){
          $output['pattern_button'] = 'FadeTail';
        }
        // Fader
        elseif ($post_html['value'] == 'Fader'){
          $output['pattern_button'] = 'Fader';
        }
        // Single Tail
        elseif ($post_html['value'] == 'SingleTail'){
          $output['pattern_button'] = 'SingleTail';
        }
        // Sequence
        elseif ($post_html['value'] == 'Sequence'){
          $output['pattern_button'] = 'Sequence';
        }
      } else {
        $output['pattern_button'] = $json['pattern_button'];
      }
    } else {
      $output['color_button'] = $json['color_button'];
      $output['pattern_button'] = $json['pattern_button'];
    }

    if (array_key_exists('color_value', $post_html)){
      $value = str_replace('#', '', $post_html['color_value']);
      $output['g'] = hexdec(sprintf("%s%s", $value[0], $value[1]));
      $output['r'] = hexdec(sprintf("%s%s", $value[2], $value[3]));
      $output['b'] = hexdec(sprintf("%s%s", $value[4], $value[5]));
      $output['color_button'] = 'solid';
    } else {
      $output['g'] = $json['g'];
      $output['r'] = $json['r'];
      $output['b'] = $json['b'];
    }

    // Reset R,G,B since the webapp does not know about them.
    $output['html'] = $post_html;
    file_put_contents("/mnt/ram/php_debug.txt", print_r($output, true));
    file_put_contents("/mnt/ram/jquery_output.txt", print_r($_POST, true));
    return $output;
  }

  ////////////////// MAIN //////////////////

  // Read RAM file and decode JSON.
  $input = read_file();

  // Update RAM input with changes from web page
  $output = build_json($input);

  // Save changes to RAM file
  write_file($output);

?>
